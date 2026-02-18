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


def test_healthy_with_disease_label_value_flags() -> None:
    flags = consistency_validate({"disease": "Healthy"}, "disease: diabetes")
    assert flags == [HEALTHY_DISEASE_CONFLICT]


def test_healthy_with_ontology_match_flags() -> None:
    matches = {
        "disease": {
            "status": "MATCHED",
            "matched_label": "cancer",
            "match_type": "label_exact",
            "score": 1.0,
        }
    }
    flags = consistency_validate(
        {"disease": "Healthy"},
        "No disease terms provided.",
        ontology_matches=matches,
    )
    assert flags == [HEALTHY_DISEASE_CONFLICT]


def test_organism_mismatch_flags() -> None:
    flags = consistency_validate(
        {"organism": "Mus musculus"},
        "Sample Organism: Homo sapiens\nStudy of mixed samples.",
    )
    assert flags == [ORGANISM_CONTEXT_CONFLICT]


def test_clean_case_ok() -> None:
    flags = consistency_validate(
        {"data_type": "RNA-seq", "disease": "Healthy", "organism": "Homo sapiens"},
        "Healthy tissue from human donors.",
    )
    assert flags == []


def test_organism_ignores_non_structured_context_mentions() -> None:
    flags = consistency_validate(
        {"organism": "Homo sapiens"},
        (
            "Sample Organism: Homo sapiens\n"
            "Platform: Illumina NovaSeq 6000 (Mus musculus)\n"
            "Protocol mentions mouse controls."
        ),
    )
    assert flags == []


def test_organism_missing_sample_context_does_not_flag() -> None:
    flags = consistency_validate(
        {"organism": "Homo sapiens"},
        "Study includes Mus musculus references in protocol text.",
    )
    assert flags == []


def test_organism_synonym_normalization_conflict() -> None:
    flags = consistency_validate(
        {"organism": "human"},
        "Sample Organism: mouse",
    )
    assert flags == [ORGANISM_CONTEXT_CONFLICT]
