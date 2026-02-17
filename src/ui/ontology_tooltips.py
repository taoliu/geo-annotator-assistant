"""Helpers for ontology tooltip rendering in the curator UI."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

COMPOSITE_MATCHED_VIA = "composite_all_components_required"
COMPOSITE_PARTIAL_MATCHED_VIA = "composite_partial_components"
_COMPOSITE_MATCHED_VIAS = {
    COMPOSITE_MATCHED_VIA,
    COMPOSITE_PARTIAL_MATCHED_VIA,
}


def _as_nonempty_str(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    if not normalized:
        return None
    return normalized


def _as_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if value.is_integer():
            return int(value)
        return None
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.isdigit():
            return int(stripped)
    return None


def is_composite_match(match: Mapping[str, object] | None) -> bool:
    if not isinstance(match, Mapping):
        return False
    matched_via = _as_nonempty_str(match.get("matched_via"))
    return bool(matched_via and matched_via in _COMPOSITE_MATCHED_VIAS)


def build_composite_tooltip_payload(
    match: Mapping[str, object] | None,
) -> dict[str, str] | None:
    if not is_composite_match(match):
        return None
    assert isinstance(match, Mapping)

    matched_via = _as_nonempty_str(match.get("matched_via")) or ""
    composite_resolution = match.get("composite_resolution")
    if not isinstance(composite_resolution, Mapping):
        selection_rule = _as_nonempty_str(match.get("selection_rule")) or ""
        return {
            "matched_via": matched_via,
            "selection_rule": selection_rule,
            "components_key": "Matched components",
            "components_value": "(not available)",
        }

    selection_rule = _as_nonempty_str(
        composite_resolution.get("selection_rule")
    ) or _as_nonempty_str(match.get("selection_rule")) or ""
    fragment_matches = composite_resolution.get("fragment_matches")
    fragments = fragment_matches if isinstance(fragment_matches, list) else []

    matched_components = _as_int(composite_resolution.get("matched_components"))
    total_components = _as_int(composite_resolution.get("total_components"))
    if total_components is None:
        total_components = len(fragments) if fragments else None
    if matched_components is None:
        matched_components = 0
        for entry in fragments:
            if isinstance(entry, Mapping):
                status = _as_nonempty_str(entry.get("status"))
                if status and status.upper() == "MATCHED":
                    matched_components += 1

    components_key = "Matched components"
    if (
        isinstance(matched_components, int)
        and isinstance(total_components, int)
        and total_components >= 0
    ):
        components_key = f"Matched components ({matched_components}/{total_components})"

    lines: list[str] = []
    for entry in fragments:
        if not isinstance(entry, Mapping):
            continue
        label = _as_nonempty_str(entry.get("label")) or _as_nonempty_str(
            entry.get("matched_label")
        )
        term_id = _as_nonempty_str(entry.get("term_id")) or _as_nonempty_str(
            entry.get("matched_term_id")
        )
        if label:
            line = f"• {label}"
            if term_id:
                line = f"{line} ({term_id})"
            lines.append(line)
            continue
        if term_id:
            lines.append(f"• ({term_id})")

    if not lines:
        for entry in fragments:
            if not isinstance(entry, Mapping):
                continue
            raw_fragment = _as_nonempty_str(entry.get("raw_fragment"))
            if raw_fragment:
                lines.append(f"• {raw_fragment}")

    return {
        "matched_via": matched_via,
        "selection_rule": selection_rule,
        "components_key": components_key,
        "components_value": "\n".join(lines) if lines else "(not available)",
    }


__all__ = [
    "COMPOSITE_MATCHED_VIA",
    "COMPOSITE_PARTIAL_MATCHED_VIA",
    "build_composite_tooltip_payload",
    "is_composite_match",
]
