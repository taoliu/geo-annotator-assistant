"""Audit record builder."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from .state import PipelineState


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def build_audit_record(state: PipelineState) -> Dict[str, Any]:
    state_dict = state.to_dict()
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
        "timestamp": _utc_timestamp(),
    }
