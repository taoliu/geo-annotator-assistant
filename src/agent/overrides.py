"""Loader for overrides.jsonl curation inputs."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

_OUTPUT_FIELDS = (
    "gse_accession",
    "gsm_accession",
    "data_type",
    "organism",
    "tissue_type",
    "cell_line",
    "disease",
    "treatment",
)

_GSM_ACCESSION_RE = re.compile(r"^GSM[0-9]+$")

OverrideValue = str | list[str]


@dataclass(frozen=True)
class OverrideRecord:
    gsm_accession: str
    field: str
    new_value: OverrideValue
    reason: str | None = None
    curator: str | None = None
    timestamp: str | None = None


def _validate_optional_string(
    record: dict, key: str, line_number: int, errors: list[str]
) -> str | None:
    if key not in record:
        return None
    value = record.get(key)
    if not isinstance(value, str):
        errors.append(f"Line {line_number}: key '{key}' must be a string")
        return None
    return value


def _validate_new_value(
    value: object, line_number: int, errors: list[str]
) -> OverrideValue | None:
    if value is None:
        errors.append(f"Line {line_number}: new_value must be non-null")
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return list(value)
    errors.append(f"Line {line_number}: new_value must be a string or list of strings")
    return None


def _validate_record(record: object, line_number: int) -> tuple[OverrideRecord | None, list[str]]:
    errors: list[str] = []
    if not isinstance(record, dict):
        return None, [f"Line {line_number}: expected a JSON object"]

    gsm_accession: str | None = None
    if "gsm_accession" not in record:
        errors.append(f"Line {line_number}: missing key 'gsm_accession'")
    else:
        value = record.get("gsm_accession")
        if not isinstance(value, str):
            errors.append(f"Line {line_number}: key 'gsm_accession' must be a string")
        elif not _GSM_ACCESSION_RE.match(value):
            errors.append(f"Line {line_number}: gsm_accession must match ^GSM[0-9]+$")
        else:
            gsm_accession = value

    field: str | None = None
    if "field" not in record:
        errors.append(f"Line {line_number}: missing key 'field'")
    else:
        value = record.get("field")
        if not isinstance(value, str):
            errors.append(f"Line {line_number}: key 'field' must be a string")
        elif value not in _OUTPUT_FIELDS:
            errors.append(
                f"Line {line_number}: field '{value}' is not a valid output field"
            )
        else:
            field = value

    new_value: OverrideValue | None = None
    if "new_value" not in record:
        errors.append(f"Line {line_number}: missing key 'new_value'")
    else:
        new_value = _validate_new_value(record.get("new_value"), line_number, errors)

    reason = _validate_optional_string(record, "reason", line_number, errors)
    curator = _validate_optional_string(record, "curator", line_number, errors)
    timestamp = _validate_optional_string(record, "timestamp", line_number, errors)

    if errors:
        return None, errors

    assert gsm_accession is not None
    assert field is not None
    assert new_value is not None

    return (
        OverrideRecord(
            gsm_accession=gsm_accession,
            field=field,
            new_value=new_value,
            reason=reason,
            curator=curator,
            timestamp=timestamp,
        ),
        [],
    )


def load_overrides(path: str) -> dict[tuple[str, str], OverrideRecord]:
    """Load overrides.jsonl records; blank lines are ignored and comments are unsupported."""
    overrides: dict[tuple[str, str], OverrideRecord] = {}
    errors: list[str] = []
    path_obj = Path(path)

    with path_obj.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                record = json.loads(stripped)
            except json.JSONDecodeError as exc:
                errors.append(f"Line {line_number}: invalid JSON ({exc.msg})")
                continue

            normalized, record_errors = _validate_record(record, line_number)
            if record_errors:
                errors.extend(record_errors)
                continue

            key = (normalized.gsm_accession, normalized.field)
            if key in overrides:
                errors.append(
                    "Line "
                    f"{line_number}: duplicate override for ({normalized.gsm_accession}, {normalized.field})"
                )
                continue

            overrides[key] = normalized

    if errors:
        raise ValueError(f"Invalid {path_obj.name}:\n" + "\n".join(errors))

    print(
        f"[OVERRIDES] Loaded {len(overrides)} override records from {path_obj.name}"
    )
    return overrides
