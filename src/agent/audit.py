"""Audit record builder."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from .state import PipelineState
from validator.failure_codes import select_primary_failure_across_fields

_FORMAT_FIELD = "__format__"
_CONSISTENCY_FIELD = "__consistency__"


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _build_failures_by_field(state_dict: Dict[str, Any]) -> Dict[str, list[str]]:
    failures: Dict[str, list[str]] = {}
    semantic_errors = state_dict.get("semantic_errors") or {}
    for field, errors in semantic_errors.items():
        if errors:
            failures[field] = list(errors)
    ontology_failures = state_dict.get("ontology_failures") or {}
    for field, failure_code in ontology_failures.items():
        if failure_code:
            failures.setdefault(field, []).append(failure_code)
    format_errors = state_dict.get("format_errors") or []
    if format_errors:
        failures[_FORMAT_FIELD] = list(format_errors)
    consistency_flags = state_dict.get("consistency_flags") or []
    if consistency_flags:
        failures[_CONSISTENCY_FIELD] = list(consistency_flags)
    return failures


def _resolve_primary_failure(state_dict: Dict[str, Any]) -> str | None:
    repair_history = state_dict.get("repair_history") or []
    for entry in repair_history:
        if isinstance(entry, dict):
            failure_code = entry.get("failure_code")
            if failure_code:
                return failure_code
    failures_by_field = _build_failures_by_field(state_dict)
    if failures_by_field:
        try:
            _, failure_code = select_primary_failure_across_fields(failures_by_field)
        except ValueError:
            return None
        return failure_code
    return None


def _ontology_status_by_field(state_dict: Dict[str, Any]) -> Dict[str, str]:
    statuses: Dict[str, str] = {}
    matches = state_dict.get("ontology_matches") or {}
    if isinstance(matches, dict):
        for field, match in matches.items():
            status = None
            if isinstance(match, dict):
                status = match.get("status")
            else:
                status = getattr(match, "status", None)
            if status:
                statuses[field] = status
    return statuses


def build_audit_record(state: PipelineState) -> Dict[str, Any]:
    state_dict = state.to_dict()
    rationale = {
        "final_decision": state_dict["final_decision"],
        "primary_failure": _resolve_primary_failure(state_dict),
        "terminal_fallback_fields": state_dict.get("terminal_fallback_fields", []),
        "n_llm_calls": len(state_dict.get("llm_raw_outputs") or []),
        "attempts_by_field": state_dict.get("attempts_by_field", {}),
        "ontology_status_by_field": _ontology_status_by_field(state_dict),
        "flags": list(state_dict.get("flags", [])),
    }
    return {
        "gsm_accession": state_dict["gsm_accession"],
        "gse_accession": state_dict["gse_accession"],
        "input_hash": state_dict["input_hash"],
        "versions": state_dict["versions"],
        "llm_raw_outputs": state_dict["llm_raw_outputs"],
        "llm_parsed_outputs": state_dict["llm_parsed_outputs"],
        "validation": {
            "format_errors": state_dict["format_errors"],
            "semantic_errors": state_dict["semantic_errors"],
            "consistency_flags": state_dict["consistency_flags"],
            "ontology_matches": state_dict["ontology_matches"],
            "ontology_failures": state_dict["ontology_failures"],
        },
        "repair_history": state_dict["repair_history"],
        "attempts_by_field": state_dict["attempts_by_field"],
        "final_output": state_dict["final_output"],
        "final_decision": state_dict["final_decision"],
        "flags": state_dict["flags"],
        "rationale": rationale,
        "timestamp": _utc_timestamp(),
    }
