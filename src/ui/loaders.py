"""JSONL loaders for UI review artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator

from ui.schema import (
    CANONICAL_FIELDS,
    CANONICAL_FIELDS_SET,
    CurationFields,
    AuditRecord,
    EvidenceRecord,
    NormalizedCurationRecord,
    SuggestionRecord,
)


def _error_prefix(path: Path, line_number: int) -> str:
    return f"{path}:{line_number}"


def _iter_jsonl_records(path: str) -> Iterator[tuple[int, dict[str, Any]]]:
    path_obj = Path(path)
    with path_obj.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                record = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"{_error_prefix(path_obj, line_number)}: invalid JSON ({exc.msg})"
                ) from exc
            if not isinstance(record, dict):
                raise ValueError(
                    f"{_error_prefix(path_obj, line_number)}: expected a JSON object"
                )
            yield line_number, record


def load_jsonl(path: str) -> list[dict[str, Any]]:
    """Load a JSONL file with line-numbered parse errors."""
    records: list[dict[str, Any]] = []
    for _, record in _iter_jsonl_records(path):
        records.append(record)
    return records


def _require_string(
    record: dict[str, Any], key: str, path: Path, line_number: int
) -> str:
    if key not in record:
        raise ValueError(f"{_error_prefix(path, line_number)}: missing key '{key}'")
    value = record.get(key)
    if not isinstance(value, str):
        raise ValueError(
            f"{_error_prefix(path, line_number)}: key '{key}' must be a string"
        )
    return value


def _extract_curation_fields(
    record: dict[str, Any], path: Path, line_number: int
) -> CurationFields:
    fields: dict[str, str] = {}
    for key in CANONICAL_FIELDS:
        fields[key] = _require_string(record, key, path, line_number)
    return fields  # type: ignore[return-value]


def load_curation_jsonl(path: str) -> list[NormalizedCurationRecord]:
    """Load and normalize curation.jsonl records."""
    path_obj = Path(path)
    normalized: list[NormalizedCurationRecord] = []
    for line_number, record in _iter_jsonl_records(path):
        gse_accession = _require_string(record, "gse_accession", path_obj, line_number)
        gsm_accession = _require_string(record, "gsm_accession", path_obj, line_number)
        fields = _extract_curation_fields(record, path_obj, line_number)
        normalized.append(
            {
                "gse_accession": gse_accession,
                "gsm_accession": gsm_accession,
                "fields": fields,
                "raw": dict(record),
            }
        )
    normalized.sort(key=lambda item: (item["gse_accession"], item["gsm_accession"]))
    return normalized


def load_evidence_jsonl(path: str) -> list[EvidenceRecord]:
    """Load evidence.jsonl records with minimal indexing keys."""
    path_obj = Path(path)
    normalized: list[EvidenceRecord] = []
    for line_number, record in _iter_jsonl_records(path):
        gse_accession = _require_string(record, "gse_accession", path_obj, line_number)
        gsm_accession = _require_string(record, "gsm_accession", path_obj, line_number)
        normalized.append(
            {
                "gse_accession": gse_accession,
                "gsm_accession": gsm_accession,
                "raw": dict(record),
            }
        )
    normalized.sort(key=lambda item: (item["gse_accession"], item["gsm_accession"]))
    return normalized


def load_suggestions_jsonl_optional(path: str) -> list[SuggestionRecord]:
    """Load suggestions.jsonl if present; returns an empty list when missing."""
    path_obj = Path(path)
    if not path_obj.exists():
        print(f"[UI] suggestions.jsonl not found at {path_obj}; returning 0 records")
        return []

    normalized: list[SuggestionRecord] = []
    for line_number, record in _iter_jsonl_records(path):
        gse_accession = _require_string(record, "gse_accession", path_obj, line_number)
        gsm_accession = _require_string(record, "gsm_accession", path_obj, line_number)
        field = _require_string(record, "field", path_obj, line_number)
        if field not in CANONICAL_FIELDS_SET:
            raise ValueError(
                f"{_error_prefix(path_obj, line_number)}: field '{field}' is not a valid suggestion field"
            )
        normalized.append(
            {
                "gse_accession": gse_accession,
                "gsm_accession": gsm_accession,
                "field": field,
                "raw": dict(record),
            }
        )
    normalized.sort(
        key=lambda item: (
            item["gse_accession"],
            item["field"],
            item["gsm_accession"],
        )
    )
    return normalized


def load_audit_jsonl_optional(path: str) -> list[AuditRecord]:
    """Load audit.jsonl if present; returns an empty list when missing."""
    path_obj = Path(path)
    if not path_obj.exists():
        print(f"[UI] audit.jsonl not found at {path_obj}; returning 0 records")
        return []

    normalized: list[AuditRecord] = []
    for line_number, record in _iter_jsonl_records(path):
        gse_accession = _require_string(record, "gse_accession", path_obj, line_number)
        gsm_accession = _require_string(record, "gsm_accession", path_obj, line_number)
        normalized.append(
            {
                "gse_accession": gse_accession,
                "gsm_accession": gsm_accession,
                "raw": dict(record),
            }
        )
    normalized.sort(key=lambda item: (item["gse_accession"], item["gsm_accession"]))
    return normalized


def load_gse_field_values_jsonl_optional(path: str) -> dict[str, Any] | None:
    """Load gse_field_values.jsonl if present; returns None when missing."""
    path_obj = Path(path)
    if not path_obj.exists():
        print(f"[UI] gse_field_values.jsonl not found at {path_obj}; skipping")
        return None
    records = load_jsonl(path)
    if not records:
        return None
    if len(records) > 1:
        print(
            "[UI] gse_field_values.jsonl contained multiple records; using first."
        )
    return records[0]


__all__ = [
    "load_jsonl",
    "load_curation_jsonl",
    "load_evidence_jsonl",
    "load_suggestions_jsonl_optional",
    "load_audit_jsonl_optional",
    "load_gse_field_values_jsonl_optional",
]
