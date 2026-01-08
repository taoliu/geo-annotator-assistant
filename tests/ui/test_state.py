from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ui.state import (
    build_table_rows,
    filter_table_rows,
    group_suggestions_by_field,
    index_evidence_records,
    index_suggestion_records,
    lookup_evidence,
    lookup_suggestions,
)


def _curation_record(gse: str, gsm: str, tissue: str) -> dict:
    return {
        "gse_accession": gse,
        "gsm_accession": gsm,
        "fields": {
            "data_type": "RNA-seq",
            "organism": "Homo sapiens",
            "tissue_type": tissue,
            "cell_line": "No",
            "disease": "Healthy",
            "treatment": "No",
        },
        "raw": {"gse_accession": gse, "gsm_accession": gsm},
    }


def test_filter_rows_by_gse_and_search() -> None:
    records = [
        _curation_record("GSE1", "GSM1", "Blood"),
        _curation_record("GSE2", "GSM2", "Liver"),
        _curation_record("GSE1", "GSM3", "Blood"),
    ]
    rows = build_table_rows(records)

    filtered = filter_table_rows(rows, "GSE1", "blood")

    assert [row["gsm_accession"] for row in filtered] == ["GSM1", "GSM3"]


def test_filter_preserves_order() -> None:
    records = [
        _curation_record("GSE1", "GSM2", "Blood"),
        _curation_record("GSE1", "GSM1", "Blood"),
    ]
    rows = build_table_rows(records)

    filtered = filter_table_rows(rows, "GSE1", "")

    assert [row["gsm_accession"] for row in filtered] == ["GSM2", "GSM1"]


def test_lookup_evidence_returns_record() -> None:
    evidence_records = [
        {
            "gse_accession": "GSE1",
            "gsm_accession": "GSM1",
            "raw": {"evidence": True},
        }
    ]
    lookup = index_evidence_records(evidence_records)

    record = lookup_evidence(lookup, "GSE1", "GSM1")

    assert record == evidence_records[0]
    assert lookup_evidence(lookup, "GSE1", "GSM2") is None


def test_lookup_suggestions_groups_by_field() -> None:
    suggestions = [
        {
            "gse_accession": "GSE1",
            "gsm_accession": "GSM1",
            "field": "disease",
            "raw": {"field": "disease", "value": "x"},
        },
        {
            "gse_accession": "GSE1",
            "gsm_accession": "GSM1",
            "field": "tissue_type",
            "raw": {"field": "tissue_type", "value": "y"},
        },
        {
            "gse_accession": "GSE1",
            "gsm_accession": "GSM1",
            "field": "disease",
            "raw": {"field": "disease", "value": "z"},
        },
    ]
    lookup = index_suggestion_records(suggestions)

    records = lookup_suggestions(lookup, "GSE1", "GSM1")
    grouped = group_suggestions_by_field(records)

    assert [field for field, _ in grouped] == ["disease", "tissue_type"]
    assert [item["raw"]["value"] for item in grouped[0][1]] == ["x", "z"]
