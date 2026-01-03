"""JSONL reader for GSM context records."""

from __future__ import annotations

import json
from typing import Iterator

_REQUIRED_KEYS = ("context_text", "gsm_accession", "gse_accession")


def _validate_record(record: dict, line_number: int) -> dict:
    if not isinstance(record, dict):
        raise ValueError(f"Line {line_number}: expected a JSON object")
    normalized: dict = {}
    for key in _REQUIRED_KEYS:
        if key not in record:
            raise ValueError(f"Line {line_number}: missing key '{key}'")
        value = record[key]
        if not isinstance(value, str):
            raise ValueError(f"Line {line_number}: key '{key}' must be a string")
        normalized[key] = value
    return normalized


def iter_gsm_contexts(jsonl_path: str) -> Iterator[dict]:
    """Yield GSM context records from a JSONL file."""
    with open(jsonl_path, "r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                record = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Line {line_number}: invalid JSON ({exc.msg})"
                ) from exc
            yield _validate_record(record, line_number)
