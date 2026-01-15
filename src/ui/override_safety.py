"""Helpers for safe override UX in the curator UI."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypedDict

from ui.dashboard import map_field_badges
from ui.overrides import OverrideValue, OverridesForGsm, format_override_value

HIGH_CONFIDENCE_BADGES: tuple[str, ...] = (
    "LOCKED",
    "CANON",
    "TERM",
)

_BADGE_LABELS = {
    "LOCKED": "locked",
    "CANON": "canonicalized",
    "TERM": "terminal exact",
}


class OverrideDiff(TypedDict):
    field: str
    backend_value: str
    override_value: str


def field_is_editable(
    edit_mode: bool,
    field: str,
    evidence_raw: Mapping[str, Any] | None,
) -> bool:
    del field, evidence_raw
    return bool(edit_mode)


def high_confidence_badges(
    field: str,
    evidence_raw: Mapping[str, Any] | None,
) -> list[str]:
    badges = map_field_badges(field, evidence_raw, {})
    return [badge for badge in badges if badge in HIGH_CONFIDENCE_BADGES]


def requires_override_confirmation(
    field: str,
    evidence_raw: Mapping[str, Any] | None,
) -> bool:
    return bool(high_confidence_badges(field, evidence_raw))


def build_override_warning(
    field: str,
    evidence_raw: Mapping[str, Any] | None,
) -> str | None:
    badges = high_confidence_badges(field, evidence_raw)
    if not badges:
        return None
    labels = [_BADGE_LABELS.get(badge, badge.lower()) for badge in badges]
    signal_text = _join_labels(labels)
    return (
        "Backend marked this value as "
        f"{signal_text}. You may override this if the annotation is incorrect."
    )


def is_field_overridden(
    overrides_for_gsm: OverridesForGsm,
    field: str,
) -> bool:
    return field in overrides_for_gsm


def build_override_diff(
    field: str,
    backend_value: OverrideValue | None,
    overrides_for_gsm: OverridesForGsm,
) -> OverrideDiff | None:
    if field not in overrides_for_gsm:
        return None
    return {
        "field": field,
        "backend_value": _format_value(backend_value),
        "override_value": _format_value(overrides_for_gsm[field]),
    }


def _format_value(value: OverrideValue | None) -> str:
    if value is None:
        return "(not available)"
    if isinstance(value, list):
        return format_override_value(value)
    if isinstance(value, str):
        return value
    return str(value)


def _join_labels(labels: list[str]) -> str:
    if not labels:
        return ""
    if len(labels) == 1:
        return labels[0]
    if len(labels) == 2:
        return f"{labels[0]} and {labels[1]}"
    return ", ".join(labels[:-1]) + f", and {labels[-1]}"


__all__ = [
    "HIGH_CONFIDENCE_BADGES",
    "OverrideDiff",
    "build_override_diff",
    "build_override_warning",
    "field_is_editable",
    "high_confidence_badges",
    "is_field_overridden",
    "requires_override_confirmation",
]
