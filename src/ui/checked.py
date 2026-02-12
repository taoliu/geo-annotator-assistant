"""Helpers for explicit checked-marker batch actions in the curator UI."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

SelectionKey = tuple[str, str]


def build_visible_checked_updates(
    rows: Sequence[Mapping[str, object]],
    checked: bool,
) -> dict[SelectionKey, bool]:
    updates: dict[SelectionKey, bool] = {}
    for row in rows:
        gse = row.get("gse_accession")
        gsm = row.get("gsm_accession")
        if not isinstance(gse, str) or not isinstance(gsm, str):
            continue
        updates[(gse, gsm)] = checked
    return updates


def merge_visible_checked_updates(
    existing: Mapping[SelectionKey, bool],
    rows: Sequence[Mapping[str, object]],
    checked: bool,
) -> tuple[dict[SelectionKey, bool], dict[SelectionKey, bool]]:
    updates = build_visible_checked_updates(rows, checked)
    visible_keys = set(updates.keys())
    merged = {
        key: value for key, value in existing.items() if key not in visible_keys
    }
    merged.update(updates)
    changes = {
        key: value for key, value in merged.items() if existing.get(key) != value
    }
    return merged, changes


__all__ = ["build_visible_checked_updates", "merge_visible_checked_updates"]
