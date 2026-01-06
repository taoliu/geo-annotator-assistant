from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from validator.failure_codes import select_primary_failure_across_fields


def test_evidence_first_beats_ontology_low_confidence_same_field() -> None:
    failures_by_field = {
        "cell_line": [
            "ontology_low_confidence_cell_line",
            "cell_line_inferred_without_evidence",
        ],
    }
    assert select_primary_failure_across_fields(failures_by_field) == (
        "cell_line",
        "cell_line_inferred_without_evidence",
    )


def test_evidence_first_beats_other_field_ontology() -> None:
    failures_by_field = {
        "cell_line": ["ontology_low_confidence_cell_line"],
        "disease": ["disease_inferred_without_evidence"],
    }
    assert select_primary_failure_across_fields(failures_by_field) == (
        "disease",
        "disease_inferred_without_evidence",
    )


def test_no_evidence_failures_uses_existing_ranking() -> None:
    failures_by_field = {
        "cell_line": ["ontology_low_confidence_cell_line"],
        "disease": ["ontology_low_confidence_disease"],
    }
    assert select_primary_failure_across_fields(failures_by_field) == (
        "disease",
        "ontology_low_confidence_disease",
    )


def test_tissue_cell_type_beats_ontology_low_confidence() -> None:
    failures_by_field = {
        "tissue_type": [
            "ontology_low_confidence_tissue_type",
            "tissue_type_is_cell_type",
        ],
    }
    assert select_primary_failure_across_fields(failures_by_field) == (
        "tissue_type",
        "tissue_type_is_cell_type",
    )
