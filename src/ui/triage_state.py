"""Session-backed state helpers for triage controls."""

from __future__ import annotations

from collections.abc import Mapping, Sequence


def _normalize_list(values: object) -> list[str]:
    if not isinstance(values, list):
        return []
    normalized: list[str] = []
    for value in values:
        if isinstance(value, str) and value and value not in normalized:
            normalized.append(value)
    return normalized


def normalize_triage_state(
    raw_state: object,
    *,
    decision_options: Sequence[str],
    sort_options: Sequence[str],
) -> dict[str, object]:
    decision_default = decision_options[0]
    sort_default = sort_options[0]
    if not isinstance(raw_state, Mapping):
        raw_state = {}
    decision = raw_state.get("decision")
    if not isinstance(decision, str) or decision not in decision_options:
        decision = decision_default
    sort_by = raw_state.get("sort_by")
    if not isinstance(sort_by, str) or sort_by not in sort_options:
        sort_by = sort_default
    sort_desc_raw = raw_state.get("sort_desc")
    sort_desc = sort_desc_raw if isinstance(sort_desc_raw, bool) else True
    return {
        "decision": decision,
        "primary": _normalize_list(raw_state.get("primary")),
        "flags": _normalize_list(raw_state.get("flags")),
        "sort_by": sort_by,
        "sort_desc": sort_desc,
    }


def merge_options_with_selected(
    options: Sequence[str],
    selected: Sequence[str],
) -> list[str]:
    merged = list(options)
    seen = set(merged)
    for value in selected:
        if isinstance(value, str) and value and value not in seen:
            merged.append(value)
            seen.add(value)
    return merged


__all__ = ["merge_options_with_selected", "normalize_triage_state"]
