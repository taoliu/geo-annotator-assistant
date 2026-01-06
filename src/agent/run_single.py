"""Single-GSM pipeline runner with stubbed parser/LLM support."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from agent.audit import build_audit_record
from agent.prompts import load_prompt
from agent.repair_loop import apply_repairs
from agent.state import PipelineState
from validator.consistency_validator import (
    ASSAY_PLATFORM_CONFLICT,
    HEALTHY_DISEASE_CONFLICT,
    ORGANISM_CONTEXT_CONFLICT,
    SINGLE_CELL_EVIDENCE_MISSING,
    consistency_validate,
)
from validator.decision_engine import decide_next_action, load_decision_table
from validator.format_validator import validate_format
from validator.ontology_validator import ground_all_fields
from validator.semantic_validator import semantic_validate
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
        field = _CONSISTENCY_FIELD_MAP.get(flag)
        if field:
            failures.setdefault(field, []).append(flag)
    return failures


def _increment_attempts(state: PipelineState, field: str) -> None:
    state.attempts_by_field[field] = state.attempts_by_field.get(field, 0) + 1


def _total_attempts(state: PipelineState) -> int:
    return sum(state.attempts_by_field.values())


def _update_validation_state(
    state: PipelineState,
    parsed_output: Dict[str, str],
    context_text: str,
    cfg: dict,
) -> None:
    state.semantic_errors = semantic_validate(parsed_output, context_text)
    state.consistency_flags = consistency_validate(parsed_output, context_text)

    rag_cfg = cfg.get("rag", {}) if isinstance(cfg, dict) else {}
    matches, ontology_failures = ground_all_fields(
        parsed_output,
        context_text,
        rag_cfg,
    )
    state.ontology_matches = {
        field: match.to_dict() if hasattr(match, "to_dict") else match
        for field, match in matches.items()
    }
    state.ontology_failures = _filter_missing_grounders(ontology_failures)


def _generate_with_format_repairs(
    state: PipelineState,
    client,
    context_text: str,
    cfg: dict,
    prompt_loader,
) -> tuple[Optional[Dict[str, str]], List[str]]:
    last_errors: List[str] = []
    word_limits = cfg.get("limits", {}).get("field_word_limits")
    label_prompt = _load_label_prompt(cfg)
    final_prompt = f"{label_prompt}\n\n{context_text}"
    raw_output = client.generate(final_prompt)
    state.llm_raw_outputs.append(raw_output)

    parsed_output, format_errors = validate_format(
        raw_output,
        REQUIRED_KEYS,
        word_limits=word_limits,
    )
    if parsed_output is not None:
        state.llm_parsed_outputs.append(parsed_output)
    if not format_errors:
        return parsed_output, []
    last_errors = format_errors

    max_repairs = cfg.get("limits", {}).get("max_format_repairs", 2)
    repair_template = prompt_loader("repair_format_v1")
    for _ in range(max_repairs):
        repair_prompt = (
            f"{repair_template}\n\nCONTEXT:\n{context_text}\n\nPREVIOUS_OUTPUT:\n"
            f"{raw_output}"
        )
        raw_output = client.generate(repair_prompt)
        state.llm_raw_outputs.append(raw_output)
        parsed_output, format_errors = validate_format(
            raw_output,
            REQUIRED_KEYS,
            word_limits=word_limits,
        )
        if parsed_output is not None:
            state.llm_parsed_outputs.append(parsed_output)
        if not format_errors:
            return parsed_output, []
        last_errors = format_errors

    return parsed_output, last_errors


def _run_decision_repairs(
    state: PipelineState,
    decision_table: Dict,
    llm_client,
    cfg: dict,
    context_text: str,
    prompt_loader,
    max_total_repairs: Optional[int],
) -> PipelineState:
    while True:
        failures_by_field = _build_failures_by_field(
            state.semantic_errors,
            state.ontology_failures,
            state.consistency_flags,
        )
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
            raw_output = llm_client.generate(repair_prompt)
            state.llm_raw_outputs.append(raw_output)
            parsed_output, format_errors = validate_format(raw_output, REQUIRED_KEYS)
            state.format_errors = format_errors
            if parsed_output is not None:
                state.llm_parsed_outputs.append(parsed_output)
            if parsed_output is None or format_errors:
                continue

            state.final_output = dict(parsed_output)
            state.format_errors = []
            _update_validation_state(state, state.final_output, context_text, cfg)
            continue

        state.final_decision = "FLAGGED"
        if decision.failure_code and decision.failure_code not in state.flags:
            state.flags.append(decision.failure_code)
        return state


def _run_llm_pipeline(state: PipelineState, cfg: dict) -> tuple[dict, dict, bool]:
    context_text = state.context_text
    if not context_text:
        raise ValueError("context_text is required for LLM labeling.")

    prompt_loader = _make_prompt_loader(cfg)
    llm_cfg = cfg.get("llm", {})
    client = create_llm_client(llm_cfg)

    parsed_output, format_errors = _generate_with_format_repairs(
        state,
        client,
        context_text,
        cfg,
        prompt_loader,
    )
    state.format_errors = format_errors
    if parsed_output is None or format_errors:
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

    state.final_output = dict(parsed_output)
    state.format_errors = []
    _update_validation_state(state, state.final_output, context_text, cfg)

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
        validation_callback=_refresh_validation,
    )

    state.final_output = _normalize_output(
        state.final_output or {},
        state.gsm_accession,
        state.gse_accession,
    )
    if state.final_decision is None:
        unresolved = bool(state.semantic_errors) or bool(state.ontology_failures) or bool(
            state.consistency_flags
        )
        state.final_decision = "FLAGGED" if unresolved else "ACCEPT"

    audit_record = build_audit_record(state)
    flagged = state.final_decision != "ACCEPT"
    return state.final_output, audit_record, flagged


def run_single_gsm(gsm_accession: str, cfg: dict) -> tuple[dict, dict, bool]:
    state = PipelineState(
        gsm_accession=gsm_accession,
        versions=dict(cfg.get("versions", {})),
    )

    parser_cfg = cfg.get("parser", {})
    if parser_cfg.get("mode") == "stub":
        context_text, parsed_jsonl, gse_accession = _stub_parse(gsm_accession)
    else:
        raise ValueError(f"Unsupported parser mode: {parser_cfg.get('mode')}")

    state.context_text = context_text
    state.parsed_jsonl = parsed_jsonl
    state.gse_accession = gse_accession
    return _run_llm_pipeline(state, cfg)


def run_single_from_context_record(
    record: dict,
    cfg: dict,
) -> tuple[dict, dict, bool]:
    gsm_accession = record["gsm_accession"]
    gse_accession = record["gse_accession"]
    context_text = record["context_text"]

    state = PipelineState(
        gsm_accession=gsm_accession,
        gse_accession=gse_accession,
        versions=dict(cfg.get("versions", {})),
    )
    state.context_text = context_text
    return _run_llm_pipeline(state, cfg)
