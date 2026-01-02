from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from validator.consistency_validator import (
    ASSAY_PLATFORM_CONFLICT,
    HEALTHY_DISEASE_CONFLICT,
    ORGANISM_CONTEXT_CONFLICT,
    SINGLE_CELL_EVIDENCE_MISSING,
    consistency_validate,
)


def test_scrna_seq_without_single_cell_cues_flags() -> None:
    flags = consistency_validate({"data_type": "scRNA-seq"}, "Bulk RNA extracted.")
    assert flags == [SINGLE_CELL_EVIDENCE_MISSING]


def test_scrna_seq_with_single_cell_cues_ok() -> None:
    flags = consistency_validate({"data_type": "scRNA-seq"}, "Single-cell prep using 10x.")
    assert flags == []


def test_microarray_with_sequencing_cues_flags() -> None:
    flags = consistency_validate({"data_type": "Microarray"}, "RNA-seq on NextSeq platform.")
    assert flags == [ASSAY_PLATFORM_CONFLICT]


def test_healthy_with_disease_cues_flags() -> None:
    flags = consistency_validate({"disease": "Healthy"}, "Cancer samples were used.")
    assert flags == [HEALTHY_DISEASE_CONFLICT]


def test_organism_mismatch_flags() -> None:
    flags = consistency_validate({"organism": "Mus musculus"}, "Study of Homo sapiens tissue.")
    assert flags == [ORGANISM_CONTEXT_CONFLICT]


def test_clean_case_ok() -> None:
    flags = consistency_validate(
        {"data_type": "RNA-seq", "disease": "Healthy", "organism": "Homo sapiens"},
        "Healthy tissue from human donors.",
    )
    assert flags == []
