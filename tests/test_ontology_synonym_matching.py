from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rag.ontology_retrieve import OntologyCandidate
from validator.ontology_match import OntologyThresholds, choose_best_ontology_candidate


def test_disease_synonym_exact_match() -> None:
    candidate = OntologyCandidate(
        term_id="DOID:1040",
        label="chronic lymphocytic leukemia",
        source="Human Disease Ontology",
        definition=None,
        synonyms=["CLL"],
        ancestors=[],
        distance=0.1,
    )

    result = choose_best_ontology_candidate("CLL", [candidate], OntologyThresholds())

    assert result.status == "MATCHED"
    assert result.match_type == "synonym_norm_exact"
    assert result.matched_via == "synonym_norm"
    assert result.matched_synonym == "CLL"
    assert result.confidence == 1.0


def test_label_exact_match() -> None:
    candidate = OntologyCandidate(
        term_id="EFO:0000001",
        label="B cell",
        source="Experimental Factor Ontology",
        definition=None,
        synonyms=["B-cell"],
        ancestors=[],
        distance=0.1,
    )

    result = choose_best_ontology_candidate("B cell", [candidate], OntologyThresholds())

    assert result.status == "MATCHED"
    assert result.match_type == "label_exact"
    assert result.matched_via == "label"
    assert result.matched_synonym is None
    assert result.confidence == 1.0


def test_normalization_handles_punctuation() -> None:
    candidate = OntologyCandidate(
        term_id="EFO:0002772",
        label="RNA-Seq",
        source="Experimental Factor Ontology",
        definition=None,
        synonyms=[],
        ancestors=[],
        distance=0.1,
    )

    result = choose_best_ontology_candidate("RNA seq", [candidate], OntologyThresholds())

    assert result.status == "MATCHED"
    assert result.match_type == "label_exact"
    assert result.matched_via == "label"
    assert result.confidence == 1.0


def test_no_synonym_falls_back_to_existing_logic() -> None:
    candidate = OntologyCandidate(
        term_id="EFO:0000002",
        label="unrelated label",
        source="Experimental Factor Ontology",
        definition=None,
        synonyms=[],
        ancestors=[],
        distance=0.1,
    )

    result = choose_best_ontology_candidate("completely different", [candidate], OntologyThresholds())

    assert result.status == "LOW_CONFIDENCE"
    assert result.match_type == "jaccard"
    assert result.matched_via is None
    assert result.matched_synonym is None
