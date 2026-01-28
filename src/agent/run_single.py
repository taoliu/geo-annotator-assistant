"""Single-GSM pipeline runner with stubbed parser/LLM support."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from agent.accession import override_accessions
from agent.audit import build_audit_record
from agent.ontology_canonicalization import (
    apply_disease_modifier_generalization,
    apply_tissue_placeholder_fallback,
    apply_terminal_exact_canonicalization_and_lock,
)
from agent.prompts import load_prompt
from agent.repair_loop import apply_repairs, merge_repair_output
from agent.state import PipelineState
from agent.context_fingerprint import compute_context_fingerprint
from agent.llm_cache import LLMCache, LLMCacheEntry, build_llm_cache_key
from validator.consistency_validator import (
    ASSAY_PLATFORM_CONFLICT,
    HEALTHY_DISEASE_CONFLICT,
    ORGANISM_CONTEXT_CONFLICT,
    SINGLE_CELL_EVIDENCE_MISSING,
    consistency_validate,
)
from validator.decision_engine import decide_next_action, load_decision_table
from validator.format_validator import (
    ERROR_EMPTY_VALUE,
    ERROR_MISSING_KEYS,
    ERROR_NON_STRING,
    ERROR_WORD_LIMIT,
    validate_format,
)
from validator.ontology_validator import ground_all_fields
from validator.semantic_validator import semantic_validate
from llm.base import LLMRequest
from llm.factory import create_llm_client

REQUIRED_KEYS: List[str] = [
    "gse_accession",
    "gsm_accession",
    "data_type",
    "organism",
    "tissue_type",
    "cell_line",
    "disease",
    "treatment",
]

_PROMPT_VERSION_MAP = {"v1": "label_v1.txt"}

_PLACEHOLDERS: Dict[str, str] = {
    "data_type": "Unknown",
    "organism": "Unknown",
    "tissue_type": "Unknown",
    "cell_line": "No",
    "disease": "Healthy",
    "treatment": "None",
}

_CONSISTENCY_FIELD_MAP = {
    ASSAY_PLATFORM_CONFLICT: "data_type",
    SINGLE_CELL_EVIDENCE_MISSING: "data_type",
    HEALTHY_DISEASE_CONFLICT: "disease",
    ORGANISM_CONTEXT_CONFLICT: "organism",
}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _resolve_prompt_dir(cfg: dict) -> str:
    prompt_dir = cfg.get("prompt_dir")
    if not prompt_dir:
        paths_cfg = cfg.get("paths") if isinstance(cfg.get("paths"), dict) else {}
        prompt_dir = paths_cfg.get("prompt_dir") if paths_cfg else None
    if not prompt_dir:
        prompt_dir = str(_repo_root() / "prompts")
    return prompt_dir


def _make_prompt_loader(cfg: dict):
    prompt_dir = _resolve_prompt_dir(cfg)

    def _load(prompt_name: str) -> str:
        return load_prompt(prompt_dir, prompt_name)

    return _load


def _normalize_stop_list(value: Any) -> list[str] | None:
    if not value:
        return None
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    return [str(value)]


def _resolve_format_salvage_limit(cfg: dict) -> Optional[int]:
    limits = cfg.get("limits", {}) if isinstance(cfg, dict) else {}
    raw_limit = limits.get("format_salvage_max_chars")
    if raw_limit is None:
        return None
    try:
        return int(raw_limit)
    except (TypeError, ValueError):
        return None


def _make_llm_request_builder(cfg: dict, state: PipelineState):
    llm_cfg = cfg.get("llm", {}) if isinstance(cfg, dict) else {}
    stop_list = _normalize_stop_list(llm_cfg.get("stop"))
    system_prompt = llm_cfg.get("system_prompt")
    model_id = llm_cfg.get("model_id") or llm_cfg.get("model_path")
    max_tokens = llm_cfg.get("max_tokens")
    if max_tokens is None:
        max_tokens = llm_cfg.get("max_new_tokens")
    max_tokens = int(max_tokens) if max_tokens is not None else None
    temperature = llm_cfg.get("temperature")
    temperature = float(temperature) if temperature is not None else None
    top_p = llm_cfg.get("top_p")
    top_p = float(top_p) if top_p is not None else None
    seed = llm_cfg.get("seed")
    seed = int(seed) if seed is not None else None

    def _build(prompt: str, stage: str) -> LLMRequest:
        request_id = f"{state.gsm_accession}:{len(state.llm_raw_outputs) + 1}"
        return LLMRequest(
            prompt=prompt,
            system=system_prompt,
            model=model_id,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            stop=stop_list,
            seed=seed,
            request_id=request_id,
            tags={"stage": stage},
        )

    return _build


def _load_label_prompt(cfg: dict) -> str:
    prompt_version = cfg.get("versions", {}).get("prompt_version", "v1")
    prompt_name = _PROMPT_VERSION_MAP.get(prompt_version)
    if not prompt_name:
        raise ValueError(f"Unsupported prompt_version: {prompt_version}")
    prompt_dir = _resolve_prompt_dir(cfg)
    return load_prompt(prompt_dir, prompt_name)


def _stub_parse(gsm_accession: str) -> Tuple[str, Optional[str], str]:
    gse_accession = "GSE000000"
    context_text = (
        "Series Accession: GSE000000\n"
        f"Sample ID: {gsm_accession}\n"
        "Sample Organism: Homo sapiens\n"
        "Sample Molecular: total RNA\n"
        "Sample Library Strategy: RNA-Seq\n"
    )
    return context_text, context_text, gse_accession


def _normalize_output(
    output: Optional[Dict[str, str]],
    gsm_accession: str,
    gse_accession: Optional[str],
) -> Dict[str, str]:
    base = output or {}
    normalized: Dict[str, str] = {}
    for key in REQUIRED_KEYS:
        if key == "gsm_accession":
            normalized[key] = gsm_accession
            continue
        if key == "gse_accession":
            normalized[key] = gse_accession or base.get(key) or "Unknown"
            continue
        value = base.get(key)
        if not value:
            value = _PLACEHOLDERS[key]
        normalized[key] = value
    return normalized


def _word_count(value: str) -> int:
    return len([token for token in value.strip().split() if token])


def _format_error_fields(
    parsed_output: Dict[str, str],
    format_errors: List[str],
    cfg: dict,
) -> set[str]:
    fields: set[str] = set()
    error_set = set(format_errors)
    if error_set.intersection({ERROR_MISSING_KEYS, ERROR_NON_STRING, ERROR_EMPTY_VALUE}):
        for key in REQUIRED_KEYS:
            if key not in parsed_output:
                fields.add(key)

    if ERROR_WORD_LIMIT in error_set:
        word_limits = cfg.get("limits", {}).get("field_word_limits")
        for key, value in parsed_output.items():
            if key not in REQUIRED_KEYS:
                continue
            limit = 5
            if isinstance(word_limits, dict):
                limit = word_limits.get(key, limit)
            try:
                limit = int(limit)
            except (TypeError, ValueError):
                limit = 5
            if limit > 0 and _word_count(value) > limit:
                fields.add(key)

    return fields


def _finalize_unrepaired_format_errors(
    state: PipelineState,
    parsed_output: Dict[str, str],
    context_text: str,
    cfg: dict,
) -> None:
    error_fields = _format_error_fields(parsed_output, state.format_errors, cfg)
    final_output = dict(parsed_output)
    for field in error_fields:
        if field in state.locked_fields:
            continue
        fallback = _PLACEHOLDERS.get(field)
        if fallback is not None:
            final_output[field] = fallback
    state.final_output = _normalize_output(
        final_output,
        state.gsm_accession,
        state.gse_accession,
    )
    _apply_locked_field_values(state)
    _update_validation_state(state, state.final_output, context_text, cfg)
    state.final_decision = "FLAGGED"
    if "format_unrepaired" not in state.flags:
        state.flags.append("format_unrepaired")


def _apply_locked_field_values(state: PipelineState) -> None:
    if state.final_output is None:
        return
    if not state.locked_fields:
        return
    for field, info in state.locked_fields.items():
        if not isinstance(info, dict):
            continue
        label = info.get("label")
        if isinstance(label, str) and label:
            state.final_output[field] = label


def _grounder_available(field: str) -> bool:
    try:
        if field == "data_type":
            from validator.grounders import data_type as module

            return hasattr(module, "ground_data_type")
        if field == "tissue_type":
            from validator.grounders import tissue_type as module

            return hasattr(module, "ground_tissue_type")
        if field == "cell_line":
            from validator.grounders import cell_line as module

            return hasattr(module, "ground_cell_line")
        if field == "disease":
            from validator.grounders import disease as module

            return hasattr(module, "ground_disease")
    except Exception:
        return False
    return False


def _filter_missing_grounders(ontology_failures: Dict[str, str]) -> Dict[str, str]:
    if not ontology_failures:
        return ontology_failures
    filtered = dict(ontology_failures)
    for field in list(filtered.keys()):
        if not _grounder_available(field):
            filtered.pop(field, None)
    return filtered


def _build_failures_by_field(
    semantic_errors: Dict[str, List[str]],
    ontology_failures: Dict[str, str],
    consistency_flags: List[str],
) -> Dict[str, List[str]]:
    failures: Dict[str, List[str]] = {}
    for field, errors in semantic_errors.items():
        if errors:
            failures[field] = list(errors)
    for field, failure_code in ontology_failures.items():
        if failure_code:
            failures.setdefault(field, []).append(failure_code)
    for flag in consistency_flags:
        if flag == HEALTHY_DISEASE_CONFLICT:
            continue
        field = _CONSISTENCY_FIELD_MAP.get(flag)
        if field:
            failures.setdefault(field, []).append(flag)
    return failures


def _increment_attempts(state: PipelineState, field: str) -> None:
    state.attempts_by_field[field] = state.attempts_by_field.get(field, 0) + 1


def _total_attempts(state: PipelineState) -> int:
    return sum(state.attempts_by_field.values())


def _record_llm_output(state: PipelineState, raw_output: str, *, cache_hit: bool) -> None:
    state.llm_raw_outputs.append(raw_output)
    if state.llm_cache_enabled:
        state.llm_cache_hits.append(bool(cache_hit))


def _update_validation_state(
    state: PipelineState,
    parsed_output: Dict[str, str],
    context_text: str,
    cfg: dict,
) -> None:
    preserved_disease_match = None
    if state.locked_fields.get("disease", {}).get("reason") == "disease_generalized_for_ontology":
        preserved_disease_match = state.ontology_matches.get("disease")
    preserved_tissue_match = None
    if state.locked_fields.get("tissue_type", {}).get("reason") == "tissue_type_non_anatomical_placeholder":
        preserved_tissue_match = state.ontology_matches.get("tissue_type")
    state.semantic_errors = semantic_validate(parsed_output, context_text)
    rag_cfg = cfg.get("rag", {}) if isinstance(cfg, dict) else {}
    matches, ontology_failures = ground_all_fields(
        parsed_output,
        context_text,
        rag_cfg,
    )
    if preserved_disease_match is not None:
        matches["disease"] = preserved_disease_match
        ontology_failures.pop("disease", None)
    if preserved_tissue_match is not None:
        matches["tissue_type"] = preserved_tissue_match
        ontology_failures.pop("tissue_type", None)
    state.ontology_matches = {
        field: match.to_dict() if hasattr(match, "to_dict") else match
        for field, match in matches.items()
    }
    state.ontology_failures = _filter_missing_grounders(ontology_failures)
    state.consistency_flags = consistency_validate(
        parsed_output,
        context_text,
        ontology_matches=state.ontology_matches,
    )
    apply_terminal_exact_canonicalization_and_lock(state, cfg)
    apply_disease_modifier_generalization(state, cfg)
    apply_tissue_placeholder_fallback(state, cfg)


def _apply_non_accept_flags(state: PipelineState) -> None:
    if state.final_decision == "ACCEPT" and "tissue_type_non_anatomical_placeholder" in state.flags:
        state.final_decision = "FLAGGED"


def _generate_with_format_repairs(
    state: PipelineState,
    client,
    context_text: str,
    cfg: dict,
    prompt_loader,
    request_builder,
    llm_cache: LLMCache | None = None,
) -> tuple[Optional[Dict[str, str]], List[str], str | None, bool]:
    last_errors: List[str] = []
    word_limits = cfg.get("limits", {}).get("field_word_limits")
    salvage_limit = _resolve_format_salvage_limit(cfg)
    def _record_salvage(meta: Dict[str, int | str]) -> None:
        state.repair_history.append(dict(meta))

    def _apply_cached_entry(
        entry: LLMCacheEntry,
    ) -> tuple[Optional[Dict[str, str]], List[str]]:
        for raw_output in entry.raw_outputs:
            _record_llm_output(state, raw_output, cache_hit=True)
        for parsed in entry.parsed_outputs:
            parsed_copy = override_accessions(
                dict(parsed),
                state.gse_accession,
                state.gsm_accession,
            )
            state.llm_parsed_outputs.append(parsed_copy)
        state.repair_history = [dict(item) for item in entry.repair_history]
        state.attempts_by_field = dict(entry.attempts_by_field)
        state.terminal_fallback_fields = set(entry.terminal_fallback_fields)
        state.semantic_errors = {
            field: list(errors) for field, errors in entry.semantic_errors.items()
        }
        state.consistency_flags = list(entry.consistency_flags)
        state.ontology_matches = copy.deepcopy(entry.ontology_matches)
        state.ontology_failures = dict(entry.ontology_failures)
        state.canonicalizations = copy.deepcopy(entry.canonicalizations)
        state.locked_fields = copy.deepcopy(entry.locked_fields)
        state.flags = list(entry.flags)
        if entry.final_output is not None:
            state.final_output = override_accessions(
                dict(entry.final_output),
                state.gse_accession,
                state.gsm_accession,
            )
        state.final_decision = entry.final_decision
        state.validation_cache_hit = True
        state.grounding_cache_hit = True
        parsed_output = None
        if entry.parsed_outputs:
            parsed_output = override_accessions(
                dict(entry.parsed_outputs[-1]),
                state.gse_accession,
                state.gsm_accession,
            )
        return parsed_output, list(entry.format_errors)

    label_prompt = _load_label_prompt(cfg)
    final_prompt = f"{label_prompt}\n\n{context_text}"
    request = request_builder(final_prompt, "label")
    cache_key = None
    cache_hit = False
    if llm_cache is not None and state.gse_accession:
        prompt_version = cfg.get("versions", {}).get("prompt_version", "v1")
        prompt_name = _PROMPT_VERSION_MAP.get(prompt_version) or str(prompt_version)
        rag_cfg = cfg.get("rag", {}) if isinstance(cfg.get("rag"), dict) else {}
        cache_key = build_llm_cache_key(
            gse_accession=state.gse_accession,
            context_fingerprint=compute_context_fingerprint(context_text),
            request=request,
            versions=dict(cfg.get("versions", {})),
            prompt_name=prompt_name,
            validation_config=rag_cfg,
        )
        cached_entry = llm_cache.get(cache_key)
        if cached_entry is not None:
            parsed_output, format_errors = _apply_cached_entry(cached_entry)
            cache_hit = True
            return parsed_output, format_errors, cache_key, cache_hit

    raw_result = client.generate(request)
    raw_output = raw_result.text
    _record_llm_output(state, raw_output, cache_hit=False)

    parsed_output, format_errors = validate_format(
        raw_output,
        REQUIRED_KEYS,
        word_limits=word_limits,
        salvage_limit=salvage_limit,
        repair_recorder=_record_salvage,
    )
    if parsed_output is not None:
        parsed_output = override_accessions(
            parsed_output,
            state.gse_accession,
            state.gsm_accession,
        )
        state.llm_parsed_outputs.append(parsed_output)
    if not format_errors:
        return parsed_output, [], cache_key, cache_hit
    last_errors = format_errors

    max_repairs = cfg.get("limits", {}).get("max_format_repairs", 2)
    repair_template = prompt_loader("repair_format_v1")
    for _ in range(max_repairs):
        repair_prompt = (
            f"{repair_template}\n\nCONTEXT:\n{context_text}\n\nPREVIOUS_OUTPUT:\n"
            f"{raw_output}"
        )
        request = request_builder(repair_prompt, "repair_format")
        raw_result = client.generate(request)
        raw_output = raw_result.text
        _record_llm_output(state, raw_output, cache_hit=False)
        parsed_output, format_errors = validate_format(
            raw_output,
            REQUIRED_KEYS,
            word_limits=word_limits,
            salvage_limit=salvage_limit,
            repair_recorder=_record_salvage,
        )
        if parsed_output is not None:
            parsed_output = override_accessions(
                parsed_output,
                state.gse_accession,
                state.gsm_accession,
            )
            state.llm_parsed_outputs.append(parsed_output)
        if not format_errors:
            return parsed_output, [], cache_key, cache_hit
        last_errors = format_errors

    return parsed_output, last_errors, cache_key, cache_hit


def _run_decision_repairs(
    state: PipelineState,
    decision_table: Dict,
    llm_client,
    cfg: dict,
    context_text: str,
    prompt_loader,
    request_builder,
    max_total_repairs: Optional[int],
) -> PipelineState:
    while True:
        failures_by_field = _build_failures_by_field(
            state.semantic_errors,
            state.ontology_failures,
            state.consistency_flags,
        )
        if state.locked_fields:
            for locked_field in list(state.locked_fields):
                failures_by_field.pop(locked_field, None)
        if not failures_by_field:
            state.final_decision = "ACCEPT"
            return state

        if max_total_repairs is not None and _total_attempts(state) >= max_total_repairs:
            state.final_decision = "FLAGGED"
            if "max_repairs_exceeded" not in state.flags:
                state.flags.append("max_repairs_exceeded")
            return state

        decision = decide_next_action(
            failures_by_field,
            state.attempts_by_field,
            decision_table,
        )

        if decision.decision_type == "ACCEPT":
            state.final_decision = "ACCEPT"
            if failures_by_field and decision.failure_code:
                if decision.failure_code not in state.flags:
                    state.flags.append(decision.failure_code)
            return state

        if decision.decision_type == "ESCALATE":
            state.final_decision = "FLAGGED"
            if decision.failure_code and decision.failure_code not in state.flags:
                state.flags.append(decision.failure_code)
            return state

        field = decision.field
        if not field:
            state.final_decision = "FLAGGED"
            if decision.failure_code and decision.failure_code not in state.flags:
                state.flags.append(decision.failure_code)
            return state

        if decision.decision_type in {"FALLBACK", "REPAIR"} and field in state.locked_fields:
            state.semantic_errors.pop(field, None)
            state.ontology_failures.pop(field, None)
            continue

        if decision.decision_type == "FALLBACK":
            if state.final_output is None:
                state.final_output = {}
            state.final_output[field] = decision.fallback_value
            _increment_attempts(state, field)
            state.repair_history.append(
                {
                    "failure_code": decision.failure_code,
                    "field": field,
                    "fallback_value": decision.fallback_value,
                }
            )
            state.format_errors = []
            _update_validation_state(state, state.final_output, context_text, cfg)
            continue

        if decision.decision_type == "REPAIR":
            _increment_attempts(state, field)
            state.repair_history.append(
                {
                    "failure_code": decision.failure_code,
                    "field": field,
                    "repair_template": decision.repair_template,
                }
            )
            if llm_client is None or context_text is None:
                continue
            if not decision.repair_template:
                state.final_decision = "FLAGGED"
                if decision.failure_code and decision.failure_code not in state.flags:
                    state.flags.append(decision.failure_code)
                return state

            try:
                repair_template = prompt_loader(decision.repair_template)
            except Exception:
                if "repair_template_missing" not in state.flags:
                    state.flags.append("repair_template_missing")
                if state.repair_history:
                    state.repair_history[-1]["template_missing"] = True
                continue
            previous_output = state.final_output or {}
            repair_prompt = (
                f"{repair_template}\n\nCONTEXT:\n{context_text}\n\nPREVIOUS_OUTPUT:\n"
                f"{json.dumps(previous_output, ensure_ascii=True)}"
            )
            request = request_builder(repair_prompt, "repair_field")
            raw_result = llm_client.generate(request)
            raw_output = raw_result.text
            _record_llm_output(state, raw_output, cache_hit=False)
            parsed_output, format_errors = validate_format(raw_output, REQUIRED_KEYS)
            state.format_errors = format_errors
            if parsed_output is not None:
                parsed_output = override_accessions(
                    parsed_output,
                    state.gse_accession,
                    state.gsm_accession,
                )
                state.llm_parsed_outputs.append(parsed_output)
            if parsed_output is None or format_errors:
                continue

            merge_repair_output(state, parsed_output)
            state.format_errors = []
            _update_validation_state(state, state.final_output, context_text, cfg)
            continue

        state.final_decision = "FLAGGED"
        if decision.failure_code and decision.failure_code not in state.flags:
            state.flags.append(decision.failure_code)
        return state


def _run_llm_pipeline(
    state: PipelineState,
    cfg: dict,
    llm_client: Optional[Any] = None,
    llm_cache: LLMCache | None = None,
) -> tuple[dict, dict, bool]:
    context_text = state.context_text
    if not context_text:
        raise ValueError("context_text is required for LLM labeling.")

    prompt_loader = _make_prompt_loader(cfg)
    llm_cfg = cfg.get("llm", {})
    if llm_client is None:
        client = create_llm_client(llm_cfg)
    else:
        client = llm_client

    request_builder = _make_llm_request_builder(cfg, state)
    raw_start = len(state.llm_raw_outputs)
    parsed_start = len(state.llm_parsed_outputs)
    repair_start = len(state.repair_history)

    parsed_output, format_errors, cache_key, cache_hit = _generate_with_format_repairs(
        state,
        client,
        context_text,
        cfg,
        prompt_loader,
        request_builder,
        llm_cache=llm_cache,
    )
    state.format_errors = format_errors
    if parsed_output is None:
        state.final_decision = "FLAGGED"
        if "format_unrepaired" not in state.flags:
            state.flags.append("format_unrepaired")
        state.final_output = _normalize_output(
            {},
            state.gsm_accession,
            state.gse_accession,
        )
        audit_record = build_audit_record(state)
        return state.final_output, audit_record, True
    if format_errors:
        _finalize_unrepaired_format_errors(
            state,
            parsed_output,
            context_text,
            cfg,
        )
        audit_record = build_audit_record(state)
        return state.final_output, audit_record, True

    if state.final_output is None:
        state.final_output = dict(parsed_output)
    state.format_errors = []
    if not state.validation_cache_hit:
        _update_validation_state(state, state.final_output, context_text, cfg)
    elif state.final_output is not None and state.final_decision is not None:
        _apply_locked_field_values(state)
        _apply_non_accept_flags(state)
        audit_record = build_audit_record(state)
        flagged = state.final_decision != "ACCEPT"
        return state.final_output, audit_record, flagged

    decision_table = load_decision_table(
        str(_repo_root() / "spec" / "decision_table.yaml")
    )
    def _refresh_validation(current_state: PipelineState) -> None:
        current_state.format_errors = []
        _update_validation_state(
            current_state,
            current_state.final_output or {},
            context_text,
            cfg,
        )

    apply_repairs(
        state,
        decision_table,
        llm_client=client,
        context_text=context_text,
        prompt_loader=prompt_loader,
        max_total_repairs=cfg.get("limits", {}).get("max_total_repairs"),
        request_builder=request_builder,
        validation_callback=_refresh_validation,
        format_salvage_limit=_resolve_format_salvage_limit(cfg),
    )

    state.final_output = _normalize_output(
        state.final_output or {},
        state.gsm_accession,
        state.gse_accession,
    )
    _apply_locked_field_values(state)
    if state.final_decision is None:
        unresolved = bool(state.semantic_errors) or bool(state.ontology_failures) or bool(
            state.consistency_flags
        )
        state.final_decision = "FLAGGED" if unresolved else "ACCEPT"
    _apply_non_accept_flags(state)

    audit_record = build_audit_record(state)
    flagged = state.final_decision != "ACCEPT"
    if llm_cache is not None and cache_key and not cache_hit:
        entry = LLMCacheEntry(
            raw_outputs=list(state.llm_raw_outputs[raw_start:]),
            parsed_outputs=[
                dict(item) for item in state.llm_parsed_outputs[parsed_start:]
            ],
            format_errors=list(state.format_errors),
            repair_history=[dict(item) for item in state.repair_history[repair_start:]],
            semantic_errors={
                field: list(errors)
                for field, errors in state.semantic_errors.items()
            },
            consistency_flags=list(state.consistency_flags),
            ontology_matches=copy.deepcopy(state.ontology_matches),
            ontology_failures=dict(state.ontology_failures),
            canonicalizations=copy.deepcopy(state.canonicalizations),
            locked_fields=copy.deepcopy(state.locked_fields),
            final_output=dict(state.final_output) if state.final_output else None,
            final_decision=state.final_decision,
            flags=list(state.flags),
            attempts_by_field=dict(state.attempts_by_field),
            terminal_fallback_fields=sorted(state.terminal_fallback_fields),
        )
        llm_cache.set(cache_key, entry)
    return state.final_output, audit_record, flagged


def run_single_gsm(
    gsm_accession: str,
    cfg: dict,
    llm_client: Optional[Any] = None,
    llm_cache: LLMCache | None = None,
) -> tuple[dict, dict, bool]:
    state = PipelineState(
        gsm_accession=gsm_accession,
        versions=dict(cfg.get("versions", {})),
    )
    state.llm_cache_enabled = llm_cache is not None

    parser_cfg = cfg.get("parser", {})
    if parser_cfg.get("mode") == "stub":
        context_text, parsed_jsonl, gse_accession = _stub_parse(gsm_accession)
    else:
        raise ValueError(f"Unsupported parser mode: {parser_cfg.get('mode')}")

    state.context_text = context_text
    state.parsed_jsonl = parsed_jsonl
    state.gse_accession = gse_accession
    return _run_llm_pipeline(state, cfg, llm_client=llm_client, llm_cache=llm_cache)


def run_single_from_context_record(
    record: dict,
    cfg: dict,
    llm_client: Optional[Any] = None,
    llm_cache: LLMCache | None = None,
) -> tuple[dict, dict, bool]:
    gsm_accession = record["gsm_accession"]
    gse_accession = record["gse_accession"]
    context_text = record["context_text"]

    state = PipelineState(
        gsm_accession=gsm_accession,
        gse_accession=gse_accession,
        versions=dict(cfg.get("versions", {})),
    )
    state.llm_cache_enabled = llm_cache is not None
    state.context_text = context_text
    return _run_llm_pipeline(state, cfg, llm_client=llm_client, llm_cache=llm_cache)
