"""Failure code constants and selection helpers."""

from __future__ import annotations

from typing import Dict, List, Tuple

INVALID_JSON = "invalid_json"
MISSING_KEYS = "missing_keys"
EXTRA_KEYS = "extra_keys"
WORD_LIMIT_VIOLATION = "word_limit_violation"
ONTOLOGY_NO_MATCH = "ontology_no_match"
TISSUE_IS_CELL_TYPE = "tissue_is_cell_type"
TREATMENT_IDENTITY_LEAKAGE = "treatment_identity_leakage"
ASSAY_PLATFORM_CONFLICT = "assay_platform_conflict"
SINGLE_CELL_EVIDENCE_MISSING = "single_cell_evidence_missing"
HEALTHY_DISEASE_CONFLICT = "healthy_disease_conflict"
ORGANISM_CONTEXT_CONFLICT = "organism_context_conflict"
DISEASE_UNSUPPORTED = "disease_unsupported"
REPEATED_FAILURE = "repeated_failure"

ALL_FAILURE_CODES = [
    INVALID_JSON,
    MISSING_KEYS,
    EXTRA_KEYS,
    WORD_LIMIT_VIOLATION,
    ONTOLOGY_NO_MATCH,
    TISSUE_IS_CELL_TYPE,
    TREATMENT_IDENTITY_LEAKAGE,
    ASSAY_PLATFORM_CONFLICT,
    SINGLE_CELL_EVIDENCE_MISSING,
    HEALTHY_DISEASE_CONFLICT,
    ORGANISM_CONTEXT_CONFLICT,
    DISEASE_UNSUPPORTED,
    REPEATED_FAILURE,
]

FAILURE_SEVERITY: Dict[str, str] = {
    INVALID_JSON: "high",
    MISSING_KEYS: "high",
    EXTRA_KEYS: "high",
    WORD_LIMIT_VIOLATION: "medium",
    ONTOLOGY_NO_MATCH: "high",
    TISSUE_IS_CELL_TYPE: "medium",
    TREATMENT_IDENTITY_LEAKAGE: "medium",
    ASSAY_PLATFORM_CONFLICT: "high",
    SINGLE_CELL_EVIDENCE_MISSING: "medium",
    HEALTHY_DISEASE_CONFLICT: "high",
    ORGANISM_CONTEXT_CONFLICT: "high",
    DISEASE_UNSUPPORTED: "medium",
    REPEATED_FAILURE: "high",
}

SEVERITY_SCORE = {"low": 1, "medium": 2, "high": 3}

PRIMARY_FAILURE_ORDER: List[str] = [
    INVALID_JSON,
    MISSING_KEYS,
    EXTRA_KEYS,
    ONTOLOGY_NO_MATCH,
    ASSAY_PLATFORM_CONFLICT,
    ORGANISM_CONTEXT_CONFLICT,
    HEALTHY_DISEASE_CONFLICT,
    SINGLE_CELL_EVIDENCE_MISSING,
    REPEATED_FAILURE,
    WORD_LIMIT_VIOLATION,
    TISSUE_IS_CELL_TYPE,
    TREATMENT_IDENTITY_LEAKAGE,
    DISEASE_UNSUPPORTED,
]

PRIMARY_FAILURE_PRIORITY = {
    failure_code: index for index, failure_code in enumerate(PRIMARY_FAILURE_ORDER)
}

DEFAULT_UNKNOWN_SEVERITY_SCORE = 4
DEFAULT_UNKNOWN_PRIORITY = len(PRIMARY_FAILURE_ORDER)


def _failure_sort_key(failure_code: str) -> Tuple[int, int, str]:
    severity = FAILURE_SEVERITY.get(failure_code)
    severity_score = SEVERITY_SCORE.get(severity, DEFAULT_UNKNOWN_SEVERITY_SCORE)
    priority = PRIMARY_FAILURE_PRIORITY.get(failure_code, DEFAULT_UNKNOWN_PRIORITY)
    return (-severity_score, priority, failure_code)


def select_primary_failure(failures: List[str]) -> str:
    if not failures:
        raise ValueError("failures must be non-empty")
    return min(failures, key=_failure_sort_key)


def select_primary_failure_across_fields(
    failures_by_field: Dict[str, List[str]],
) -> Tuple[str, str]:
    if not failures_by_field:
        raise ValueError("failures_by_field must be non-empty")
    candidates = []
    for field, failures in failures_by_field.items():
        if not failures:
            continue
        primary_failure = select_primary_failure(failures)
        candidates.append((field, primary_failure))
    if not candidates:
        raise ValueError("failures_by_field must contain at least one failure")
    return min(candidates, key=lambda item: (_failure_sort_key(item[1]), item[0]))
