from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ui.loaders import (
    load_audit_jsonl_optional,
    load_curation_jsonl,
    load_jsonl,
    load_suggestions_jsonl_optional,
)
from ui.schema import CANONICAL_FIELDS


def _write_jsonl(path: Path, records: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record))
            handle.write("\n")


def _curation_record(gse: str, gsm: str, extra: str) -> dict:
    return {
        "gse_accession": gse,
        "gsm_accession": gsm,
        "data_type": "RNA-seq",
        "organism": "Homo sapiens",
        "tissue_type": "Blood",
        "cell_line": "No",
        "disease": "Healthy",
        "treatment": "No",
        "extra": extra,
    }


def test_load_curation_jsonl_normalizes_fields(tmp_path: Path) -> None:
    records = [_curation_record("GSE12345", "GSM67890", "alpha")]
    path = tmp_path / "curation.jsonl"
    _write_jsonl(path, records)

    loaded = load_curation_jsonl(str(path))

    assert len(loaded) == 1
    record = loaded[0]
    assert record["gse_accession"] == "GSE12345"
    assert record["gsm_accession"] == "GSM67890"
    assert set(record["fields"].keys()) == set(CANONICAL_FIELDS)
    assert record["fields"]["tissue_type"] == "Blood"
    assert record["raw"] == records[0]


def test_load_jsonl_reports_line_number_on_parse_error(tmp_path: Path) -> None:
    path = tmp_path / "bad.jsonl"
    path.write_text(
        json.dumps({"gse_accession": "GSE12345"}) + "\n" + "{bad\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError) as exc:
        load_jsonl(str(path))

    message = str(exc.value)
    assert str(path) in message
    assert f"{path}:2" in message


def test_load_curation_jsonl_rejects_missing_keys(tmp_path: Path) -> None:
    record = _curation_record("GSE12345", "GSM67890", "alpha")
    record.pop("gsm_accession")
    path = tmp_path / "curation.jsonl"
    _write_jsonl(path, [record])

    with pytest.raises(ValueError, match="missing key 'gsm_accession'"):
        load_curation_jsonl(str(path))


def test_load_curation_jsonl_deterministic_ordering(tmp_path: Path) -> None:
    records = [
        _curation_record("GSE2", "GSM2", "gamma"),
        _curation_record("GSE1", "GSM1", "beta"),
        _curation_record("GSE1", "GSM0", "alpha"),
    ]
    path = tmp_path / "curation.jsonl"
    _write_jsonl(path, records)

    loaded = load_curation_jsonl(str(path))

    ordered_keys = [(row["gse_accession"], row["gsm_accession"]) for row in loaded]
    assert ordered_keys == [
        ("GSE1", "GSM0"),
        ("GSE1", "GSM1"),
        ("GSE2", "GSM2"),
    ]


def test_load_suggestions_jsonl_optional_missing(tmp_path: Path) -> None:
    missing_path = tmp_path / "suggestions.jsonl"

    loaded = load_suggestions_jsonl_optional(str(missing_path))

    assert loaded == []


def test_load_audit_jsonl_optional_missing(tmp_path: Path) -> None:
    missing_path = tmp_path / "audit.jsonl"

    loaded = load_audit_jsonl_optional(str(missing_path))

    assert loaded == []
