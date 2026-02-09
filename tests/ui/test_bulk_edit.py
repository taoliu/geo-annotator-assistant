from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ui.bulk_edit import (
    apply_bulk_edit,
    build_bulk_edit_preview,
    is_empty_bulk_value,
    normalize_selected_rows,
    resolve_selected_keys,
    validate_bulk_edit,
)


def _rows() -> list[dict[str, object]]:
    return [
        {
            "gse_accession": "GSE1",
            "gsm_accession": "GSM1",
            "data_type": "RNA-seq",
            "organism": "Homo sapiens",
            "tissue_type": "Blood",
            "cell_line": "No",
            "disease": "Healthy",
            "treatment": "No",
        },
        {
            "gse_accession": "GSE1",
            "gsm_accession": "GSM2",
            "data_type": "RNA-seq",
            "organism": "Homo sapiens",
            "tissue_type": "Liver",
            "cell_line": "No",
            "disease": "Cancer",
            "treatment": "No",
        },
    ]


def test_normalize_selected_rows_filters_invalid_and_duplicates() -> None:
    assert normalize_selected_rows([1, 0, 1, -1, 5, "2"], 2) == [1, 0]


def test_resolve_selected_keys_preserves_table_order() -> None:
    keys = resolve_selected_keys(_rows(), [1, 0, 1])
    assert keys == [("GSE1", "GSM2"), ("GSE1", "GSM1")]


def test_build_bulk_edit_preview_counts_noops_and_changes() -> None:
    rows = _rows()
    overrides = {("GSE1", "GSM1", "disease"): "Flu"}

    preview = build_bulk_edit_preview(rows, [0, 1], "disease", "Flu", overrides)

    assert preview == {"selected_count": 2, "no_op_count": 1, "changed_count": 1}


def test_validate_bulk_edit_blocks_rows_requiring_confirmation() -> None:
    rows = _rows()
    evidence_lookup = {
        ("GSE1", "GSM1"): {
            "raw": {
                "locked_fields": {
                    "disease": {"reason": "ontology_terminal_exact"}
                }
            }
        },
        ("GSE1", "GSM2"): {"raw": {}},
    }

    failures = validate_bulk_edit(
        rows,
        [0, 1],
        "disease",
        evidence_lookup,
        edit_mode=True,
    )

    assert len(failures) == 1
    assert failures[0]["gse_accession"] == "GSE1"
    assert failures[0]["gsm_accession"] == "GSM1"
    assert "Backend marked this value as" in failures[0]["reason"]


def test_apply_bulk_edit_sets_and_clears_overrides() -> None:
    rows = _rows()
    overrides = {("GSE1", "GSM1", "disease"): "Flu"}

    updated, changed_count, no_op_count = apply_bulk_edit(
        rows,
        [0, 1],
        "disease",
        "Healthy",
        overrides,
    )

    assert changed_count == 2
    assert no_op_count == 0
    assert ("GSE1", "GSM1", "disease") not in updated
    assert updated[("GSE1", "GSM2", "disease")] == "Healthy"


def test_is_empty_bulk_value_handles_strings_and_lists() -> None:
    assert is_empty_bulk_value("") is True
    assert is_empty_bulk_value("   ") is True
    assert is_empty_bulk_value([]) is True
    assert is_empty_bulk_value("Healthy") is False
    assert is_empty_bulk_value(["Drug A"]) is False
