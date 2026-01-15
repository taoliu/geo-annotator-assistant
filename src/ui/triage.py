"""Table triage helpers for GSM review UI."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any, TypedDict

from ui.dashboard import map_field_badges
from ui.evidence import EVIDENCE_FIELDS
from ui.override_safety import HIGH_CONFIDENCE_BADGES
from ui.overrides import OverrideKey, OverrideValue, overrides_for_gsm
from ui.state import TableRow


NEEDS_ATTENTION_STATUSES = {"AMBIGUOUS", "LOW_CONFIDENCE", "NO_MATCH"}
TRIAGE_FILTERS: tuple[str, ...] = (
    "All",
    "Needs attention",
    "Has overrides",
    "Clean",
)


class TriageFlags(TypedDict):
    needs_attention: bool
    has_overrides: bool
    is_clean: bool


def needs_attention(evidence_raw: Mapping[str, Any] | None) -> bool:
    if not isinstance(evidence_raw, Mapping):
        return False
    for status in _iter_statuses(evidence_raw):
        if status in NEEDS_ATTENTION_STATUSES:
            return True
    return False


def has_overrides(
    overrides: Mapping[OverrideKey, OverrideValue],
    gse_accession: str,
    gsm_accession: str,
) -> bool:
    return bool(overrides_for_gsm(overrides, gse_accession, gsm_accession))


def is_clean(
    evidence_raw: Mapping[str, Any] | None,
    overrides_for_selected: Mapping[str, OverrideValue],
) -> bool:
    if overrides_for_selected:
        return False
    if not isinstance(evidence_raw, Mapping):
        return False
    if needs_attention(evidence_raw):
        return False
    for field in EVIDENCE_FIELDS:
        badges = map_field_badges(field, evidence_raw, {})
        if not _has_high_confidence_signal(badges):
            return False
    return True


def build_triage_flags(
    rows: Iterable[TableRow],
    evidence_lookup: Mapping[tuple[str, str], Mapping[str, Any]],
    overrides: Mapping[OverrideKey, OverrideValue],
) -> dict[tuple[str, str], TriageFlags]:
    triage: dict[tuple[str, str], TriageFlags] = {}
    for row in rows:
        key = (row["gse_accession"], row["gsm_accession"])
        evidence = evidence_lookup.get(key)
        evidence_raw = None
        if isinstance(evidence, Mapping):
            evidence_raw = evidence.get("raw")
        overrides_for_selected = overrides_for_gsm(
            overrides, row["gse_accession"], row["gsm_accession"]
        )
        triage[key] = {
            "needs_attention": needs_attention(evidence_raw),
            "has_overrides": bool(overrides_for_selected),
            "is_clean": is_clean(evidence_raw, overrides_for_selected),
        }
    return triage


def apply_triage_filter(
    rows: Iterable[TableRow],
    triage_flags: Mapping[tuple[str, str], TriageFlags],
    mode: str,
) -> list[TableRow]:
    if mode == "All":
        return list(rows)
    filtered: list[TableRow] = []
    for row in rows:
        key = (row["gse_accession"], row["gsm_accession"])
        flags = triage_flags.get(
            key,
            {"needs_attention": False, "has_overrides": False, "is_clean": False},
        )
        if mode == "Needs attention" and flags["needs_attention"]:
            filtered.append(row)
        elif mode == "Has overrides" and flags["has_overrides"]:
            filtered.append(row)
        elif mode == "Clean" and flags["is_clean"]:
            filtered.append(row)
    return filtered


def _iter_statuses(evidence_raw: Mapping[str, Any]) -> list[str]:
    statuses: list[str] = []
    evidence_by_field = evidence_raw.get("evidence_by_field")
    if isinstance(evidence_by_field, Mapping):
        for field_info in evidence_by_field.values():
            if isinstance(field_info, Mapping):
                status = _normalize_status(field_info.get("ontology_status"))
                if status:
                    statuses.append(status)
    rationale = evidence_raw.get("rationale")
    if isinstance(rationale, Mapping):
        status_map = rationale.get("ontology_status_by_field")
        if isinstance(status_map, Mapping):
            for status in status_map.values():
                normalized = _normalize_status(status)
                if normalized:
                    statuses.append(normalized)
    grounding = evidence_raw.get("grounding")
    if isinstance(grounding, Mapping):
        for match in grounding.values():
            if isinstance(match, Mapping):
                status = _normalize_status(match.get("status"))
                if status:
                    statuses.append(status)
    validation = evidence_raw.get("validation")
    if isinstance(validation, Mapping):
        ontology_matches = validation.get("ontology_matches")
        if isinstance(ontology_matches, Mapping):
            for match in ontology_matches.values():
                if isinstance(match, Mapping):
                    status = _normalize_status(match.get("status"))
                    if status:
                        statuses.append(status)
    return statuses


def _normalize_status(status: Any) -> str:
    if not isinstance(status, str):
        return ""
    return status.strip().upper()


def _has_high_confidence_signal(badges: list[str]) -> bool:
    return any(badge in HIGH_CONFIDENCE_BADGES for badge in badges)


__all__ = [
    "NEEDS_ATTENTION_STATUSES",
    "TRIAGE_FILTERS",
    "TriageFlags",
    "apply_triage_filter",
    "build_triage_flags",
    "has_overrides",
    "is_clean",
    "needs_attention",
]
