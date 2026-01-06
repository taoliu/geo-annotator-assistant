from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from validator.semantic_validator import (
    CELL_LINE_INFERRED_WITHOUT_EVIDENCE,
    CELL_LINE_IS_CELL_TYPE,
    CELL_LINE_YES_INVALID,
    DISEASE_INFERRED_WITHOUT_EVIDENCE,
    TISSUE_TYPE_IS_CELL_TYPE,
    TREATMENT_IDENTITY_LEAKAGE,
    semantic_validate,
)


def test_tissue_type_cell_type_flagged() -> None:
    errors = semantic_validate({"tissue_type": "intestinal epithelial cells"}, "")
    assert errors == {"tissue_type": [TISSUE_TYPE_IS_CELL_TYPE]}


def test_tissue_type_tissue_ok() -> None:
    errors = semantic_validate({"tissue_type": "Small intestine"}, "")
    assert errors == {}


def test_treatment_identity_leakage() -> None:
    errors = semantic_validate({"treatment": "Lgr5-GFP cells, no treatment"}, "")
    assert errors == {"treatment": [TREATMENT_IDENTITY_LEAKAGE]}


def test_treatment_none_ok() -> None:
    errors = semantic_validate({"treatment": "None"}, "")
    assert errors == {}


def test_cell_line_yes_invalid() -> None:
    errors = semantic_validate({"cell_line": "Yes"}, "")
    assert errors == {"cell_line": [CELL_LINE_YES_INVALID]}


def test_cell_line_cell_type_detected() -> None:
    errors = semantic_validate({"cell_line": "CD8+ T cells"}, "")
    assert errors == {"cell_line": [CELL_LINE_IS_CELL_TYPE]}


def test_cell_line_pbmc_detected() -> None:
    errors = semantic_validate({"cell_line": "PBMC"}, "")
    assert errors == {"cell_line": [CELL_LINE_IS_CELL_TYPE]}


def test_cell_line_without_context_evidence() -> None:
    errors = semantic_validate(
        {"cell_line": "HepG2"},
        "Primary hepatocyte samples profiled with RNA-seq.",
    )
    assert errors == {"cell_line": [CELL_LINE_INFERRED_WITHOUT_EVIDENCE]}


def test_disease_without_context_cues() -> None:
    errors = semantic_validate({"disease": "Breast cancer"}, "Sample from healthy tissue.")
    assert errors == {"disease": [DISEASE_INFERRED_WITHOUT_EVIDENCE]}


def test_disease_with_context_cues() -> None:
    errors = semantic_validate({"disease": "Breast cancer"}, "Patient has breast cancer.")
    assert errors == {}
