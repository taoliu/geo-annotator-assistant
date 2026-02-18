"""Evidence extraction helpers for UI field panels."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypedDict

EVIDENCE_FIELDS: tuple[str, ...] = (
    "data_type",
    "tissue_type",
    "cell_line",
    "disease",
)

_TERMINAL_EXACT_TYPES = {
    "label_exact",
    "label_norm_exact",
    "synonym_exact",
    "synonym_norm_exact",
    "term_id_exact",
}

_NORMALIZED_VALUE_KEYS = (
    "normalized_value",
    "normalized_raw_value",
    "cleaned_value",
    "cleaned_raw_value",
)

_SOURCE_KEYS = (
    "selected_source",
    "matched_source",
    "ontology",
)


class EvidenceItem(TypedDict):
    label: str
    value: str


def extract_field_evidence(
    field: str,
    evidence_raw: Mapping[str, Any] | None,
) -> list[EvidenceItem]:
    if not isinstance(evidence_raw, Mapping):
        return []

    match_info = _lookup_match_info(field, evidence_raw)
    items: list[EvidenceItem] = []

    _append_item(items, "Raw value", _format_value(_get_value(match_info, "raw_value")))
    _append_item(
        items,
        "Normalized value",
        _format_value(_get_first_value(match_info, _NORMALIZED_VALUE_KEYS)),
    )
    _append_item(
        items,
        "Ontology source",
        _format_value(_get_first_value(match_info, _SOURCE_KEYS)),
    )

    status = _resolve_status(field, evidence_raw, match_info)
    _append_item(items, "Match status", _format_value(status))
    _append_item(
        items,
        "Match type",
        _format_value(_get_value(match_info, "match_type")),
    )
    _append_item(items, "Score", _format_value(_get_value(match_info, "score")))

    canonical_label = _resolve_canonical_label(field, evidence_raw, match_info)
    _append_item(
        items,
        "Canonical label used",
        _format_value(canonical_label),
    )

    if _resolve_locked(field, evidence_raw, match_info):
        _append_item(items, "Locked", "true")

    if _resolve_terminal_exact(match_info):
        _append_item(items, "Terminal exact", "true")

    return items


def _lookup_match_info(
    field: str,
    evidence_raw: Mapping[str, Any],
) -> Mapping[str, Any] | None:
    grounding = evidence_raw.get("grounding")
    if isinstance(grounding, Mapping):
        field_info = grounding.get(field)
        if isinstance(field_info, Mapping):
            return field_info

    validation = evidence_raw.get("validation")
    if isinstance(validation, Mapping):
        ontology_matches = validation.get("ontology_matches")
        if isinstance(ontology_matches, Mapping):
            field_info = ontology_matches.get(field)
            if isinstance(field_info, Mapping):
                return field_info

    return None


def _resolve_status(
    field: str,
    evidence_raw: Mapping[str, Any],
    match_info: Mapping[str, Any] | None,
) -> str | None:
    if isinstance(match_info, Mapping):
        status = _normalize_status(match_info.get("status"))
        if status:
            return status

    evidence_by_field = evidence_raw.get("evidence_by_field")
    if isinstance(evidence_by_field, Mapping):
        field_info = evidence_by_field.get(field)
        if isinstance(field_info, Mapping):
            status = _normalize_status(field_info.get("ontology_status"))
            if status:
                return status

    rationale = evidence_raw.get("rationale")
    if isinstance(rationale, Mapping):
        statuses = rationale.get("ontology_status_by_field")
        if isinstance(statuses, Mapping):
            status = _normalize_status(statuses.get(field))
            if status:
                return status

    return None


def _resolve_canonical_label(
    field: str,
    evidence_raw: Mapping[str, Any],
    match_info: Mapping[str, Any] | None,
) -> str | None:
    if isinstance(match_info, Mapping):
        label_used = _format_value(match_info.get("canonical_label_used"))
        if label_used:
            return label_used

    canonicalizations = evidence_raw.get("canonicalizations")
    if isinstance(canonicalizations, list):
        for entry in canonicalizations:
            if not isinstance(entry, Mapping):
                continue
            if entry.get("field") != field:
                continue
            canonical_value = _format_value(entry.get("canonical_value"))
            if canonical_value:
                return canonical_value
    return None


def _resolve_locked(
    field: str,
    evidence_raw: Mapping[str, Any],
    match_info: Mapping[str, Any] | None,
) -> bool:
    locked_fields = evidence_raw.get("locked_fields")
    if isinstance(locked_fields, Mapping) and locked_fields.get(field):
        return True

    if isinstance(match_info, Mapping) and match_info.get("locked") is True:
        return True

    return False


def _resolve_terminal_exact(match_info: Mapping[str, Any] | None) -> bool:
    if not isinstance(match_info, Mapping):
        return False
    status = match_info.get("status")
    score = match_info.get("score")
    match_type = match_info.get("match_type")
    if not isinstance(status, str) or not isinstance(match_type, str):
        return False
    if status != "MATCHED" or match_type not in _TERMINAL_EXACT_TYPES:
        return False
    try:
        numeric_score = float(score)
    except (TypeError, ValueError):
        return False
    return numeric_score == 1.0


def _normalize_status(status: Any) -> str:
    if not isinstance(status, str):
        return ""
    return status.strip().upper()


def _append_item(items: list[EvidenceItem], label: str, value: str | None) -> None:
    if value is None:
        return
    if value == "":
        return
    items.append({"label": label, "value": value})


def _get_value(match_info: Mapping[str, Any] | None, key: str) -> Any:
    if not isinstance(match_info, Mapping):
        return None
    return match_info.get(key)


def _get_first_value(match_info: Mapping[str, Any] | None, keys: tuple[str, ...]) -> Any:
    if not isinstance(match_info, Mapping):
        return None
    for key in keys:
        value = match_info.get(key)
        formatted = _format_value(value)
        if formatted:
            return formatted
    return None


def _format_value(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        return stripped
    return str(value)


__all__ = ["EVIDENCE_FIELDS", "EvidenceItem", "extract_field_evidence"]
