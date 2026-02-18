"""Pipeline state for per-GSM annotation runs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


def _serialize_ontology_matches(matches: Dict[str, Any]) -> Dict[str, Any]:
    serialized: Dict[str, Any] = {}
    for field_name, match in matches.items():
        if hasattr(match, "to_dict") and callable(getattr(match, "to_dict")):
            serialized[field_name] = match.to_dict()
        else:
            serialized[field_name] = match
    return serialized


@dataclass
class PipelineState:
    gsm_accession: str
    gse_accession: Optional[str] = None
    input_hash: Optional[str] = None
    parsed_jsonl: Optional[str] = None
    context_text: Optional[str] = None

    llm_raw_outputs: List[str] = field(default_factory=list)
    llm_parsed_outputs: List[Dict[str, Any]] = field(default_factory=list)
    llm_cache_hits: List[bool] = field(default_factory=list)
    llm_cache_enabled: bool = False
    validation_cache_hit: bool = False
    grounding_cache_hit: bool = False

    format_errors: List[str] = field(default_factory=list)
    format_error_details: List[Dict[str, Any]] = field(default_factory=list)
    semantic_errors: Dict[str, List[str]] = field(default_factory=dict)
    consistency_flags: List[str] = field(default_factory=list)
    ontology_matches: Dict[str, Any] = field(default_factory=dict)
    ontology_failures: Dict[str, str] = field(default_factory=dict)
    canonicalizations: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    locked_fields: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    attempts_by_field: Dict[str, int] = field(default_factory=dict)
    repair_history: List[Dict[str, Any]] = field(default_factory=list)
    terminal_fallback_fields: set[str] = field(default_factory=set)

    final_output: Optional[Dict[str, str]] = None
    final_decision: Optional[str] = None
    flags: List[str] = field(default_factory=list)

    versions: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gsm_accession": self.gsm_accession,
            "gse_accession": self.gse_accession,
            "input_hash": self.input_hash,
            "parsed_jsonl": self.parsed_jsonl,
            "context_text": self.context_text,
            "llm_raw_outputs": list(self.llm_raw_outputs),
            "llm_parsed_outputs": list(self.llm_parsed_outputs),
            "llm_cache_hits": list(self.llm_cache_hits),
            "llm_cache_enabled": self.llm_cache_enabled,
            "validation_cache_hit": self.validation_cache_hit,
            "grounding_cache_hit": self.grounding_cache_hit,
            "format_errors": list(self.format_errors),
            "format_error_details": [dict(item) for item in self.format_error_details],
            "semantic_errors": {
                field_name: list(errors)
                for field_name, errors in self.semantic_errors.items()
            },
            "consistency_flags": list(self.consistency_flags),
            "ontology_matches": _serialize_ontology_matches(self.ontology_matches),
            "ontology_failures": dict(self.ontology_failures),
            "canonicalizations": [
                self.canonicalizations[key] for key in sorted(self.canonicalizations)
            ],
            "locked_fields": {
                key: self.locked_fields[key] for key in sorted(self.locked_fields)
            },
            "attempts_by_field": dict(self.attempts_by_field),
            "repair_history": list(self.repair_history),
            "terminal_fallback_fields": sorted(self.terminal_fallback_fields),
            "final_output": (
                dict(self.final_output) if self.final_output is not None else None
            ),
            "final_decision": self.final_decision,
            "flags": list(self.flags),
            "versions": dict(self.versions),
        }
