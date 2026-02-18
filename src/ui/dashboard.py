"""Field status dashboard helpers for the curator UI."""

from __future__ import annotations

from typing import Any, Mapping, TypedDict

from ui.overrides import OverrideValue, OverridesForGsm, format_override_value
from ui.schema import NormalizedCurationRecord

DASHBOARD_FIELDS: tuple[str, ...] = (
    "data_type",
    "organism",
    "tissue_type",
    "cell_line",
    "disease",
    "treatment",
    "gse_accession",
    "gsm_accession",
)

BADGE_ORDER: tuple[str, ...] = (
    "OVERRIDDEN",
    "LOCKED",
    "TERMINAL",
    "REPAIRED",
    "CANON",
    "TERM",
    "AMBIG",
    "NO-MATCH",
)

BADGE_TOOLTIPS: dict[str, str] = {
    "OVERRIDDEN": (
        "This value was manually overridden in the current session. "
        "Overrides do not retrigger backend logic."
    ),
    "LOCKED": (
        "Backend marked this field as final due to a deterministic ontology match "
        "or policy rule. The system will not attempt further repair."
    ),
    "TERMINAL": (
        "This value is a policy-defined fallback (e.g. Unknown, No, Healthy). "
        "It reflects insufficient or non-actionable evidence, not correctness."
    ),
    "REPAIRED": (
        "This value was modified by the backend repair loop after validation "
        "or ontology checks."
    ),
    "CANON": (
        "Backend replaced the value with an ontology canonical label. "
        "Overrides remain allowed."
    ),
    "TERM": (
        "Ontology returned a terminal exact match for this field. "
        "Overrides remain allowed."
    ),
    "AMBIG": "Ontology match ambiguous or low confidence. Review may be needed.",
    "NO-MATCH": "Ontology match not found. Review may be needed.",
}

_TERMINAL_EXACT_TYPES = {
    "label_exact",
    "label_norm_exact",
    "synonym_exact",
    "synonym_norm_exact",
    "term_id_exact",
}

_AMBIGUOUS_STATUSES = {"LOW_CONFIDENCE", "AMBIGUOUS"}


class DashboardItem(TypedDict):
    field: str
    label: str
    value: str
    badges: list[str]


def build_dashboard_item(
    field: str,
    selection_key: tuple[str, str],
    curation: NormalizedCurationRecord | None,
    effective_fields: Mapping[str, OverrideValue] | None,
    evidence_raw: Mapping[str, Any] | None,
    overrides_for_gsm: OverridesForGsm,
) -> DashboardItem:
    value = resolve_display_value(
        field,
        selection_key,
        effective_fields,
        curation,
    )
    badges = map_field_badges(
        field,
        evidence_raw,
        overrides_for_gsm,
        curation.get("raw") if curation else None,
    )
    return {
        "field": field,
        "label": field,
        "value": value,
        "badges": badges,
    }


def build_dashboard_items(
    selection_key: tuple[str, str],
    curation: NormalizedCurationRecord | None,
    effective_fields: Mapping[str, OverrideValue] | None,
    evidence_raw: Mapping[str, Any] | None,
    overrides_for_gsm: OverridesForGsm,
) -> list[DashboardItem]:
    items: list[DashboardItem] = []
    for field in DASHBOARD_FIELDS:
        items.append(
            build_dashboard_item(
                field,
                selection_key,
                curation,
                effective_fields,
                evidence_raw,
                overrides_for_gsm,
            )
        )
    return items


def resolve_display_value(
    field: str,
    selection_key: tuple[str, str],
    effective_fields: Mapping[str, OverrideValue] | None,
    curation: NormalizedCurationRecord | None,
) -> str:
    if field == "gse_accession":
        return _stringify_value(selection_key[0] if selection_key else None)
    if field == "gsm_accession":
        return _stringify_value(selection_key[1] if selection_key else None)
    if effective_fields is not None and field in effective_fields:
        return _stringify_value(effective_fields.get(field))
    if curation is not None:
        value = curation.get("fields", {}).get(field)
        return _stringify_value(value)
    return _stringify_value(None)


def map_field_badges(
    field: str,
    evidence_raw: Mapping[str, Any] | None,
    overrides_for_gsm: OverridesForGsm,
    curation_raw: Mapping[str, Any] | None = None,
) -> list[str]:
    badges: set[str] = set()
    if field in overrides_for_gsm:
        badges.add("OVERRIDDEN")
    if _field_locked(field, evidence_raw):
        badges.add("LOCKED")
    if _field_terminal_fallback(field, curation_raw, evidence_raw):
        badges.add("TERMINAL")
    if _field_repaired(field, curation_raw, evidence_raw):
        badges.add("REPAIRED")
    if _field_canonicalized(field, evidence_raw):
        badges.add("CANON")
    if _field_terminal_exact(field, evidence_raw):
        badges.add("TERM")

    status = _field_ontology_status(field, evidence_raw)
    if status in _AMBIGUOUS_STATUSES:
        badges.add("AMBIG")
    if status == "NO_MATCH":
        badges.add("NO-MATCH")

    return [badge for badge in BADGE_ORDER if badge in badges]


def _field_locked(field: str, evidence_raw: Mapping[str, Any] | None) -> bool:
    if not evidence_raw:
        return False
    locked_fields = evidence_raw.get("locked_fields")
    if isinstance(locked_fields, dict) and locked_fields.get(field):
        return True
    grounding = evidence_raw.get("grounding")
    if isinstance(grounding, dict):
        field_info = grounding.get(field)
        if isinstance(field_info, dict) and field_info.get("locked") is True:
            return True
    return False


def _field_canonicalized(field: str, evidence_raw: Mapping[str, Any] | None) -> bool:
    if not evidence_raw:
        return False
    canonicalizations = evidence_raw.get("canonicalizations")
    if isinstance(canonicalizations, list):
        for entry in canonicalizations:
            if isinstance(entry, dict) and entry.get("field") == field:
                return True
    grounding = evidence_raw.get("grounding")
    if isinstance(grounding, dict):
        field_info = grounding.get(field)
        if isinstance(field_info, dict) and field_info.get("canonical_label_used"):
            return True
    return False


def _field_terminal_fallback(
    field: str,
    curation_raw: Mapping[str, Any] | None,
    evidence_raw: Mapping[str, Any] | None,
) -> bool:
    if isinstance(curation_raw, Mapping):
        terminal_fields = curation_raw.get("terminal_fallback_fields")
        if isinstance(terminal_fields, list) and field in terminal_fields:
            return True
    if not evidence_raw:
        return False
    evidence_by_field = evidence_raw.get("evidence_by_field")
    if isinstance(evidence_by_field, dict):
        field_info = evidence_by_field.get(field)
        if isinstance(field_info, dict) and field_info.get("terminal_fallback") is True:
            return True
    return False


def _field_repaired(
    field: str,
    curation_raw: Mapping[str, Any] | None,
    evidence_raw: Mapping[str, Any] | None,
) -> bool:
    attempts_value = None
    if isinstance(curation_raw, Mapping):
        attempts_by_field = curation_raw.get("attempts_by_field")
        if isinstance(attempts_by_field, Mapping):
            attempts_value = attempts_by_field.get(field)
    if attempts_value is None and evidence_raw:
        evidence_by_field = evidence_raw.get("evidence_by_field")
        if isinstance(evidence_by_field, Mapping):
            field_info = evidence_by_field.get(field)
            if isinstance(field_info, Mapping):
                attempts_value = field_info.get("attempts")
    try:
        attempts = int(attempts_value)
    except (TypeError, ValueError):
        attempts = 0
    return attempts > 0


def _field_terminal_exact(field: str, evidence_raw: Mapping[str, Any] | None) -> bool:
    if not evidence_raw:
        return False
    for match in _iter_ontology_matches(field, evidence_raw):
        status = match.get("status")
        score = match.get("score")
        match_type = match.get("match_type")
        if _is_terminal_exact(status, score, match_type):
            return True
    return False


def _iter_ontology_matches(
    field: str, evidence_raw: Mapping[str, Any]
) -> list[Mapping[str, Any]]:
    matches: list[Mapping[str, Any]] = []
    grounding = evidence_raw.get("grounding")
    if isinstance(grounding, dict):
        field_info = grounding.get(field)
        if isinstance(field_info, dict):
            matches.append(field_info)
    validation = evidence_raw.get("validation")
    if isinstance(validation, dict):
        ontology_matches = validation.get("ontology_matches")
        if isinstance(ontology_matches, dict):
            field_info = ontology_matches.get(field)
            if isinstance(field_info, dict):
                matches.append(field_info)
    return matches


def _field_ontology_status(
    field: str, evidence_raw: Mapping[str, Any] | None
) -> str:
    if not evidence_raw:
        return ""
    evidence_by_field = evidence_raw.get("evidence_by_field")
    if isinstance(evidence_by_field, dict):
        field_info = evidence_by_field.get(field)
        if isinstance(field_info, dict):
            status = field_info.get("ontology_status")
            normalized = _normalize_status(status)
            if normalized:
                return normalized
    rationale = evidence_raw.get("rationale")
    if isinstance(rationale, dict):
        statuses = rationale.get("ontology_status_by_field")
        if isinstance(statuses, dict):
            status = statuses.get(field)
            normalized = _normalize_status(status)
            if normalized:
                return normalized
    grounding = evidence_raw.get("grounding")
    if isinstance(grounding, dict):
        field_info = grounding.get(field)
        if isinstance(field_info, dict):
            status = field_info.get("status")
            normalized = _normalize_status(status)
            if normalized:
                return normalized
    validation = evidence_raw.get("validation")
    if isinstance(validation, dict):
        ontology_matches = validation.get("ontology_matches")
        if isinstance(ontology_matches, dict):
            field_info = ontology_matches.get(field)
            if isinstance(field_info, dict):
                status = field_info.get("status")
                normalized = _normalize_status(status)
                if normalized:
                    return normalized
    return ""


def _is_terminal_exact(status: Any, score: Any, match_type: Any) -> bool:
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


def _stringify_value(value: OverrideValue | None) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, list):
        return format_override_value(value)
    return str(value)


__all__ = [
    "BADGE_ORDER",
    "BADGE_TOOLTIPS",
    "DASHBOARD_FIELDS",
    "DashboardItem",
    "build_dashboard_item",
    "build_dashboard_items",
    "map_field_badges",
    "resolve_display_value",
]
