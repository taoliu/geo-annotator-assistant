from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agent.overrides import load_overrides


def _write_jsonl(path: Path, records: list[dict], trailing_blank: bool = False) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record))
            handle.write("\n")
        if trailing_blank:
            handle.write("\n")


def test_load_overrides_valid_records(capsys, tmp_path: Path) -> None:
    records = [
        {
            "gsm_accession": "GSM123456",
            "field": "organism",
            "new_value": "Homo sapiens",
            "reason": "Curator confirmed from GEO description",
            "curator": "AB",
            "timestamp": "2026-01-07T10:30:00Z",
        },
        {
            "gsm_accession": "GSM123457",
            "field": "tissue_type",
            "new_value": ["liver", "hepatocyte"],
        },
    ]
    path = tmp_path / "overrides.jsonl"
    _write_jsonl(path, records, trailing_blank=True)

    overrides = load_overrides(str(path))
    output = capsys.readouterr().out

    assert "[OVERRIDES] Loaded 2 override records from overrides.jsonl" in output
    assert len(overrides) == 2
    record = overrides[("GSM123456", "organism")]
    assert record.new_value == "Homo sapiens"
    assert record.reason == "Curator confirmed from GEO description"
    assert record.curator == "AB"
    assert record.timestamp == "2026-01-07T10:30:00Z"
    assert overrides[("GSM123457", "tissue_type")].new_value == [
        "liver",
        "hepatocyte",
    ]


def test_load_overrides_empty_file(capsys, tmp_path: Path) -> None:
    path = tmp_path / "overrides.jsonl"
    path.write_text("", encoding="utf-8")

    overrides = load_overrides(str(path))
    output = capsys.readouterr().out

    assert overrides == {}
    assert "[OVERRIDES] Loaded 0 override records from overrides.jsonl" in output


def test_load_overrides_accumulates_errors(tmp_path: Path) -> None:
    records = [
        {
            "gsm_accession": "BAD123",
            "field": "organism",
            "new_value": "Homo sapiens",
        },
        {
            "gsm_accession": "GSM123458",
            "field": "organisms",
            "new_value": "Homo sapiens",
        },
    ]
    path = tmp_path / "overrides.jsonl"
    _write_jsonl(path, records)

    with pytest.raises(ValueError) as exc:
        load_overrides(str(path))

    message = str(exc.value)
    assert "Invalid overrides.jsonl" in message
    assert "Line 1" in message
    assert "Line 2" in message


def test_load_overrides_rejects_missing_keys(tmp_path: Path) -> None:
    records = [{"gsm_accession": "GSM123459", "field": "organism"}]
    path = tmp_path / "overrides.jsonl"
    _write_jsonl(path, records)

    with pytest.raises(ValueError, match="missing key 'new_value'"):
        load_overrides(str(path))


def test_load_overrides_rejects_duplicate_records(tmp_path: Path) -> None:
    records = [
        {
            "gsm_accession": "GSM123460",
            "field": "organism",
            "new_value": "Homo sapiens",
        },
        {
            "gsm_accession": "GSM123460",
            "field": "organism",
            "new_value": "Mus musculus",
        },
    ]
    path = tmp_path / "overrides.jsonl"
    _write_jsonl(path, records)

    with pytest.raises(ValueError, match="duplicate override"):
        load_overrides(str(path))
