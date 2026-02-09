"""Bulk-edit helpers for explicit, reversible UI-only table operations."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, TypedDict

from ui.override_safety import (
    build_override_warning,
    field_is_editable,
    requires_override_confirmation,
)
from ui.overrides import OverrideValue, OverridesMap, clear_override, set_override
from ui.schema import CANONICAL_FIELDS_SET

SelectionKey = tuple[str, str]


class BulkEditPreview(TypedDict):
    selected_count: int
    no_op_count: int
    changed_count: int


class BulkEditValidationFailure(TypedDict):
    gse_accession: str
    gsm_accession: str
    reason: str


def normalize_selected_rows(
    selected_rows: object,
    row_count: int,
) -> list[int]:
    if not isinstance(selected_rows, Sequence) or row_count <= 0:
        return []
    normalized: list[int] = []
    seen: set[int] = set()
    for value in selected_rows:
        if not isinstance(value, int):
            continue
        if value < 0 or value >= row_count:
            continue
        if value in seen:
            continue
        normalized.append(value)
        seen.add(value)
    return normalized


def resolve_selected_keys(
    rows: list[dict[str, object]],
    selected_rows: list[int],
) -> list[SelectionKey]:
    keys: list[SelectionKey] = []
    seen: set[SelectionKey] = set()
    for row_idx in normalize_selected_rows(selected_rows, len(rows)):
        row = rows[row_idx]
        gse = row.get("gse_accession")
        gsm = row.get("gsm_accession")
        if not isinstance(gse, str) or not isinstance(gsm, str):
            continue
        key = (gse, gsm)
        if key in seen:
            continue
        keys.append(key)
        seen.add(key)
    return keys


def build_bulk_edit_preview(
    rows: list[dict[str, object]],
    selected_rows: list[int],
    field: str,
    new_value: OverrideValue,
    overrides: Mapping[tuple[str, str, str], OverrideValue],
) -> BulkEditPreview:
    selected = normalize_selected_rows(selected_rows, len(rows))
    if field not in CANONICAL_FIELDS_SET:
        return {
            "selected_count": len(selected),
            "no_op_count": 0,
            "changed_count": 0,
        }

    no_op_count = 0
    changed_count = 0
    for row_idx in selected:
        row = rows[row_idx]
        gse = row.get("gse_accession")
        gsm = row.get("gsm_accession")
        if not isinstance(gse, str) or not isinstance(gsm, str):
            continue
        backend_value = _normalize_value(row.get(field))
        current_value = overrides.get((gse, gsm, field), backend_value)
        if _values_match(current_value, new_value):
            no_op_count += 1
        else:
            changed_count += 1

    return {
        "selected_count": len(selected),
        "no_op_count": no_op_count,
        "changed_count": changed_count,
    }


def validate_bulk_edit(
    rows: list[dict[str, object]],
    selected_rows: list[int],
    field: str,
    evidence_lookup: Mapping[SelectionKey, dict[str, Any]],
    edit_mode: bool,
) -> list[BulkEditValidationFailure]:
    failures: list[BulkEditValidationFailure] = []
    if field not in CANONICAL_FIELDS_SET:
        return failures

    for key in resolve_selected_keys(rows, selected_rows):
        evidence = evidence_lookup.get(key)
        evidence_raw = evidence.get("raw") if isinstance(evidence, Mapping) else None

        if not field_is_editable(edit_mode, field, evidence_raw):
            failures.append(
                {
                    "gse_accession": key[0],
                    "gsm_accession": key[1],
                    "reason": f"Field '{field}' is not editable in the current mode.",
                }
            )
            continue
        if not requires_override_confirmation(field, evidence_raw):
            continue
        failures.append(
            {
                "gse_accession": key[0],
                "gsm_accession": key[1],
                "reason": (
                    build_override_warning(field, evidence_raw)
                    or "This row requires explicit override confirmation."
                ),
            }
        )
    return failures


def apply_bulk_edit(
    rows: list[dict[str, object]],
    selected_rows: list[int],
    field: str,
    new_value: OverrideValue,
    overrides: Mapping[tuple[str, str, str], OverrideValue],
) -> tuple[OverridesMap, int, int]:
    updated: OverridesMap = dict(overrides)
    changed_count = 0
    no_op_count = 0
    if field not in CANONICAL_FIELDS_SET:
        return updated, changed_count, no_op_count

    for row_idx in normalize_selected_rows(selected_rows, len(rows)):
        row = rows[row_idx]
        gse = row.get("gse_accession")
        gsm = row.get("gsm_accession")
        if not isinstance(gse, str) or not isinstance(gsm, str):
            continue
        backend_value = _normalize_value(row.get(field))
        key = (gse, gsm, field)
        current_value = updated.get(key, backend_value)
        if _values_match(current_value, new_value):
            no_op_count += 1
            continue

        if _values_match(backend_value, new_value):
            updated = clear_override(updated, gse, gsm, field)
        else:
            updated = set_override(updated, key, new_value)
        changed_count += 1

    return updated, changed_count, no_op_count


def is_empty_bulk_value(value: OverrideValue) -> bool:
    if isinstance(value, str):
        return not value.strip()
    return len(value) == 0


def _normalize_value(value: object) -> OverrideValue:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return value
    return str(value)


def _values_match(left: object, right: object) -> bool:
    if isinstance(left, str) and isinstance(right, str):
        return left.strip() == right.strip()
    return left == right


__all__ = [
    "BulkEditPreview",
    "BulkEditValidationFailure",
    "apply_bulk_edit",
    "build_bulk_edit_preview",
    "is_empty_bulk_value",
    "normalize_selected_rows",
    "resolve_selected_keys",
    "validate_bulk_edit",
]
