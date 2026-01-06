"""Failure code constants and selection helpers."""

from __future__ import annotations

from typing import Dict, List, Tuple

INVALID_JSON = "invalid_json"
MISSING_KEYS = "missing_keys"
EXTRA_KEYS = "extra_keys"
WORD_LIMIT_VIOLATION = "word_limit_violation"
ONTOLOGY_INDEX_UNAVAILABLE = "ontology_index_unavailable"
ONTOLOGY_NO_MATCH_TISSUE_TYPE = "ontology_no_match_tissue_type"
ONTOLOGY_AMBIGUOUS_TISSUE_TYPE = "ontology_ambiguous_tissue_type"
ONTOLOGY_LOW_CONFIDENCE_TISSUE_TYPE = "ontology_low_confidence_tissue_type"
ONTOLOGY_NO_MATCH_DISEASE = "ontology_no_match_disease"
ONTOLOGY_AMBIGUOUS_DISEASE = "ontology_ambiguous_disease"
ONTOLOGY_LOW_CONFIDENCE_DISEASE = "ontology_low_confidence_disease"
ONTOLOGY_NO_MATCH_CELL_LINE = "ontology_no_match_cell_line"
ONTOLOGY_AMBIGUOUS_CELL_LINE = "ontology_ambiguous_cell_line"
ONTOLOGY_LOW_CONFIDENCE_CELL_LINE = "ontology_low_confidence_cell_line"
ONTOLOGY_NO_MATCH_DATA_TYPE = "ontology_no_match_data_type"
ONTOLOGY_AMBIGUOUS_DATA_TYPE = "ontology_ambiguous_data_type"
ONTOLOGY_LOW_CONFIDENCE_DATA_TYPE = "ontology_low_confidence_data_type"
TISSUE_TYPE_IS_CELL_TYPE = "tissue_type_is_cell_type"
TREATMENT_IDENTITY_LEAKAGE = "treatment_identity_leakage"
CELL_LINE_YES_INVALID = "cell_line_yes_invalid"
CELL_LINE_IS_CELL_TYPE = "cell_line_is_cell_type"
DISEASE_INFERRED_WITHOUT_EVIDENCE = "disease_inferred_without_evidence"
CELL_LINE_INFERRED_WITHOUT_EVIDENCE = "cell_line_inferred_without_evidence"
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
    ONTOLOGY_INDEX_UNAVAILABLE,
    ONTOLOGY_NO_MATCH_TISSUE_TYPE,
    ONTOLOGY_AMBIGUOUS_TISSUE_TYPE,
    ONTOLOGY_LOW_CONFIDENCE_TISSUE_TYPE,
    ONTOLOGY_NO_MATCH_DISEASE,
    ONTOLOGY_AMBIGUOUS_DISEASE,
    ONTOLOGY_LOW_CONFIDENCE_DISEASE,
    ONTOLOGY_NO_MATCH_CELL_LINE,
    ONTOLOGY_AMBIGUOUS_CELL_LINE,
    ONTOLOGY_LOW_CONFIDENCE_CELL_LINE,
    ONTOLOGY_NO_MATCH_DATA_TYPE,
    ONTOLOGY_AMBIGUOUS_DATA_TYPE,
    ONTOLOGY_LOW_CONFIDENCE_DATA_TYPE,
    TISSUE_TYPE_IS_CELL_TYPE,
    TREATMENT_IDENTITY_LEAKAGE,
    CELL_LINE_YES_INVALID,
    CELL_LINE_IS_CELL_TYPE,
    DISEASE_INFERRED_WITHOUT_EVIDENCE,
    CELL_LINE_INFERRED_WITHOUT_EVIDENCE,
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
    ONTOLOGY_INDEX_UNAVAILABLE: "low",
    ONTOLOGY_NO_MATCH_TISSUE_TYPE: "high",
    ONTOLOGY_AMBIGUOUS_TISSUE_TYPE: "high",
    ONTOLOGY_LOW_CONFIDENCE_TISSUE_TYPE: "medium",
    ONTOLOGY_NO_MATCH_DISEASE: "high",
    ONTOLOGY_AMBIGUOUS_DISEASE: "high",
    ONTOLOGY_LOW_CONFIDENCE_DISEASE: "medium",
    ONTOLOGY_NO_MATCH_CELL_LINE: "high",
    ONTOLOGY_AMBIGUOUS_CELL_LINE: "high",
    ONTOLOGY_LOW_CONFIDENCE_CELL_LINE: "medium",
    ONTOLOGY_NO_MATCH_DATA_TYPE: "high",
    ONTOLOGY_AMBIGUOUS_DATA_TYPE: "high",
    ONTOLOGY_LOW_CONFIDENCE_DATA_TYPE: "medium",
    TISSUE_TYPE_IS_CELL_TYPE: "medium",
    TREATMENT_IDENTITY_LEAKAGE: "medium",
    CELL_LINE_YES_INVALID: "medium",
    CELL_LINE_IS_CELL_TYPE: "low",
    DISEASE_INFERRED_WITHOUT_EVIDENCE: "medium",
    CELL_LINE_INFERRED_WITHOUT_EVIDENCE: "medium",
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
    ONTOLOGY_INDEX_UNAVAILABLE,
    ONTOLOGY_NO_MATCH_TISSUE_TYPE,
    ONTOLOGY_NO_MATCH_DISEASE,
    ONTOLOGY_NO_MATCH_CELL_LINE,
    ONTOLOGY_NO_MATCH_DATA_TYPE,
    ONTOLOGY_AMBIGUOUS_TISSUE_TYPE,
    ONTOLOGY_AMBIGUOUS_DISEASE,
    ONTOLOGY_AMBIGUOUS_CELL_LINE,
    ONTOLOGY_AMBIGUOUS_DATA_TYPE,
    ONTOLOGY_LOW_CONFIDENCE_TISSUE_TYPE,
    ONTOLOGY_LOW_CONFIDENCE_DISEASE,
    ONTOLOGY_LOW_CONFIDENCE_CELL_LINE,
    ONTOLOGY_LOW_CONFIDENCE_DATA_TYPE,
    ASSAY_PLATFORM_CONFLICT,
    ORGANISM_CONTEXT_CONFLICT,
    HEALTHY_DISEASE_CONFLICT,
    SINGLE_CELL_EVIDENCE_MISSING,
    REPEATED_FAILURE,
    WORD_LIMIT_VIOLATION,
    TISSUE_TYPE_IS_CELL_TYPE,
    TREATMENT_IDENTITY_LEAKAGE,
    CELL_LINE_YES_INVALID,
    CELL_LINE_IS_CELL_TYPE,
    DISEASE_INFERRED_WITHOUT_EVIDENCE,
    CELL_LINE_INFERRED_WITHOUT_EVIDENCE,
    DISEASE_UNSUPPORTED,
]

PRIMARY_FAILURE_PRIORITY = {
    failure_code: index for index, failure_code in enumerate(PRIMARY_FAILURE_ORDER)
}

DEFAULT_UNKNOWN_SEVERITY_SCORE = 4
DEFAULT_UNKNOWN_PRIORITY = len(PRIMARY_FAILURE_ORDER)

EVIDENCE_FIRST_FAILURES = {
    DISEASE_INFERRED_WITHOUT_EVIDENCE,
    CELL_LINE_INFERRED_WITHOUT_EVIDENCE,
    TISSUE_TYPE_IS_CELL_TYPE,
}


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
    for field in sorted(failures_by_field.keys()):
        failures = failures_by_field[field]
        if not failures:
            continue
        for failure_code in failures:
            if failure_code in EVIDENCE_FIRST_FAILURES:
                return field, failure_code
    candidates = []
    for field, failures in failures_by_field.items():
        if not failures:
            continue
        primary_failure = select_primary_failure(failures)
        candidates.append((field, primary_failure))
    if not candidates:
        raise ValueError("failures_by_field must contain at least one failure")
    return min(candidates, key=lambda item: (_failure_sort_key(item[1]), item[0]))
