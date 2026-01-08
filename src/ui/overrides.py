"""In-memory override helpers for the curator UI."""

from __future__ import annotations

import json
from typing import Mapping

from ui.schema import CANONICAL_FIELDS_SET, NormalizedCurationRecord

OverrideKey = tuple[str, str, str]
OverrideValue = str | list[str]
OverridesMap = dict[OverrideKey, OverrideValue]
OverridesForGsm = dict[str, OverrideValue]


def set_override(
    overrides: Mapping[OverrideKey, OverrideValue],
    key: OverrideKey,
    value: OverrideValue,
) -> OverridesMap:
    gse, gsm, field = key
    if not isinstance(gse, str) or not isinstance(gsm, str):
        raise ValueError("Override key requires gse_accession and gsm_accession strings.")
    if not isinstance(field, str) or field not in CANONICAL_FIELDS_SET:
        raise ValueError(f"Override field must be canonical: {field!r}")
    _validate_override_value(value)

    updated = dict(overrides)
    updated[key] = value
    return updated


def clear_overrides_for_gsm(
    overrides: Mapping[OverrideKey, OverrideValue],
    gse_accession: str,
    gsm_accession: str,
) -> OverridesMap:
    return {
        key: value
        for key, value in overrides.items()
        if key[0] != gse_accession or key[1] != gsm_accession
    }


def clear_all_overrides(_: Mapping[OverrideKey, OverrideValue]) -> OverridesMap:
    return {}


def overrides_for_gsm(
    overrides: Mapping[OverrideKey, OverrideValue],
    gse_accession: str,
    gsm_accession: str,
) -> OverridesForGsm:
    selected: OverridesForGsm = {}
    for (gse, gsm, field), value in overrides.items():
        if gse == gse_accession and gsm == gsm_accession:
            selected[field] = value
    return selected


def apply_overrides_to_record(
    record: NormalizedCurationRecord | None,
    overrides_for_selected: Mapping[str, OverrideValue],
) -> dict[str, OverrideValue] | None:
    if record is None:
        return None
    effective = dict(record["fields"])
    for field, value in overrides_for_selected.items():
        if field in CANONICAL_FIELDS_SET:
            effective[field] = value
    return effective


def parse_override_input(raw_value: str) -> OverrideValue:
    value = raw_value.strip()
    if value.startswith("["):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return value
        if isinstance(parsed, list) and all(isinstance(item, str) for item in parsed):
            return parsed
    return value


def format_override_value(value: OverrideValue) -> str:
    if isinstance(value, list):
        return json.dumps(value)
    return value


def _validate_override_value(value: OverrideValue) -> None:
    if isinstance(value, str):
        return
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return
    raise ValueError("Override values must be a string or list of strings.")


__all__ = [
    "OverrideKey",
    "OverrideValue",
    "OverridesMap",
    "OverridesForGsm",
    "apply_overrides_to_record",
    "clear_all_overrides",
    "clear_overrides_for_gsm",
    "format_override_value",
    "overrides_for_gsm",
    "parse_override_input",
    "set_override",
]
