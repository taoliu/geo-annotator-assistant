"""Single-GSM pipeline runner with stubbed parser/LLM support."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from agent.audit import build_audit_record
from agent.prompts import load_prompts
from agent.repair_loop import apply_repairs
from agent.state import PipelineState
from validator.consistency_validator import (
    ASSAY_PLATFORM_CONFLICT,
    HEALTHY_DISEASE_CONFLICT,
    ORGANISM_CONTEXT_CONFLICT,
    SINGLE_CELL_EVIDENCE_MISSING,
    consistency_validate,
)
from validator.decision_engine import load_decision_table
from validator.format_validator import validate_format
from validator.ontology_validator import ground_all_fields
from validator.semantic_validator import semantic_validate

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


def _load_label_prompt(cfg: dict) -> str:
    prompt_version = cfg.get("versions", {}).get("prompt_version", "v1")
    prompt_name = _PROMPT_VERSION_MAP.get(prompt_version)
    if not prompt_name:
        raise ValueError(f"Unsupported prompt_version: {prompt_version}")

    prompt_dir = cfg.get("prompt_dir")
    if not prompt_dir:
        paths_cfg = cfg.get("paths") if isinstance(cfg.get("paths"), dict) else {}
        prompt_dir = paths_cfg.get("prompt_dir") if paths_cfg else None
    if not prompt_dir:
        prompt_dir = str(_repo_root() / "prompts")

    prompts = load_prompts(prompt_dir)
    if prompt_name not in prompts:
        raise ValueError(f"Prompt template not found: {prompt_name}")
    return prompts[prompt_name]


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


def _stub_llm_output(gsm_accession: str, gse_accession: str, llm_cfg: Dict) -> str:
    if llm_cfg.get("stub_invalid_json"):
        return "{invalid json"
    output = {
        "gse_accession": gse_accession,
        "gsm_accession": gsm_accession,
        "data_type": "RNA-seq",
        "organism": "Homo sapiens",
        "tissue_type": "Blood",
        "cell_line": "No",
        "disease": "Healthy",
        "treatment": "None",
    }
    return json.dumps(output, ensure_ascii=True)


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


def _run_repairs(
    state: PipelineState,
    failures_by_field: Dict[str, List[str]],
    decision_table: Dict,
    max_total_repairs: Optional[int],
) -> None:
    repair_state = copy.deepcopy(state)
    repair_state.semantic_errors = failures_by_field
    repair_state.ontology_failures = {}
    repair_state.consistency_flags = []

    apply_repairs(
        repair_state,
        decision_table,
        max_total_repairs=max_total_repairs,
    )

    state.final_output = repair_state.final_output
    state.final_decision = repair_state.final_decision
    state.flags = repair_state.flags
    state.attempts_by_field = repair_state.attempts_by_field
    state.repair_history = repair_state.repair_history


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

    llm_cfg = cfg.get("llm", {})
    if llm_cfg.get("mode") == "stub":
        raw_output = _stub_llm_output(gsm_accession, gse_accession, llm_cfg)
    else:
        raise ValueError(f"Unsupported LLM mode: {llm_cfg.get('mode')}")

    state.llm_raw_outputs.append(raw_output)

    parsed_output, format_errors = validate_format(raw_output, REQUIRED_KEYS)
    state.format_errors = format_errors
    state.llm_parsed_outputs.append(parsed_output or {})

    if parsed_output is None:
        state.final_decision = "FLAGGED"
        state.final_output = _normalize_output({}, gsm_accession, gse_accession)
        audit_record = build_audit_record(state)
        return state.final_output, audit_record, True

    state.semantic_errors = semantic_validate(parsed_output, context_text)
    state.consistency_flags = consistency_validate(parsed_output, context_text)

    matches, ontology_failures = ground_all_fields(
        parsed_output,
        context_text,
        cfg.get("rag", {}),
    )
    state.ontology_matches = {
        field: match.to_dict() if hasattr(match, "to_dict") else match
        for field, match in matches.items()
    }
    state.ontology_failures = _filter_missing_grounders(ontology_failures)

    failures_by_field = _build_failures_by_field(
        state.semantic_errors,
        state.ontology_failures,
        state.consistency_flags,
    )

    decision_table = load_decision_table(
        str(_repo_root() / "spec" / "decision_table.yaml")
    )

    state.final_output = dict(parsed_output)
    _run_repairs(
        state,
        failures_by_field,
        decision_table,
        cfg.get("limits", {}).get("max_total_repairs"),
    )

    state.final_output = _normalize_output(
        state.final_output or {}, gsm_accession, gse_accession
    )

    audit_record = build_audit_record(state)
    flagged = state.final_decision != "ACCEPT"
    return state.final_output, audit_record, flagged


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

    label_prompt = _load_label_prompt(cfg)
    final_prompt = f"{label_prompt}\n\n{context_text}"

    llm_cfg = cfg.get("llm", {})
    if llm_cfg.get("mode") == "stub":
        raw_output = _stub_llm_output(gsm_accession, gse_accession, llm_cfg)
    else:
        raise ValueError(f"Unsupported LLM mode: {llm_cfg.get('mode')}")

    state.llm_raw_outputs.append(raw_output)

    parsed_output, format_errors = validate_format(raw_output, REQUIRED_KEYS)
    state.format_errors = format_errors
    state.llm_parsed_outputs.append(parsed_output or {})

    if parsed_output is None:
        state.final_decision = "FLAGGED"
        state.final_output = _normalize_output({}, gsm_accession, gse_accession)
        audit_record = build_audit_record(state)
        return state.final_output, audit_record, True

    state.semantic_errors = semantic_validate(parsed_output, context_text)
    state.consistency_flags = consistency_validate(parsed_output, context_text)

    matches, ontology_failures = ground_all_fields(
        parsed_output,
        context_text,
        cfg.get("rag", {}),
    )
    state.ontology_matches = {
        field: match.to_dict() if hasattr(match, "to_dict") else match
        for field, match in matches.items()
    }
    state.ontology_failures = _filter_missing_grounders(ontology_failures)

    failures_by_field = _build_failures_by_field(
        state.semantic_errors,
        state.ontology_failures,
        state.consistency_flags,
    )

    decision_table = load_decision_table(
        str(_repo_root() / "spec" / "decision_table.yaml")
    )

    state.final_output = dict(parsed_output)
    _run_repairs(
        state,
        failures_by_field,
        decision_table,
        cfg.get("limits", {}).get("max_total_repairs"),
    )

    state.final_output = _normalize_output(
        state.final_output or {}, gsm_accession, gse_accession
    )

    audit_record = build_audit_record(state)
    flagged = state.final_decision != "ACCEPT"
    return state.final_output, audit_record, flagged
