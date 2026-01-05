from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rag.ontology_retrieve import _build_candidate
from validator.ontology_match import OntologyThresholds, choose_best_ontology_candidate


def test_synonym_propagation_from_metadata() -> None:
    meta = {
        "term_id": "DOID:1040",
        "label": "chronic lymphocytic leukemia",
        "synonyms": ["CLL"],
        "source": "Human Disease Ontology",
    }
    candidate = _build_candidate("DOID:1040", 0.1, meta, None, "Human Disease Ontology")

    assert candidate.synonyms == ["CLL"]

    thresholds = OntologyThresholds(min_confidence_to_accept=1.1, max_delta_for_ambiguity=0.05)
    result = choose_best_ontology_candidate("CLL", [candidate], thresholds)

    assert result.status == "MATCHED"
    assert result.match_type == "synonym_exact"
    assert result.matched_synonym == "CLL"
    assert result.matched_via == "synonym"
    assert result.best is not None
    assert result.best.term_id == "DOID:1040"
    assert result.confidence == 1.0


def test_synonym_exact_tie_break_prefers_more_specific_label() -> None:
    meta_short = {
        "term_id": "DOID:1036",
        "label": "chronic leukemia",
        "synonyms": ["CLL"],
        "source": "Human Disease Ontology",
    }
    meta_long = {
        "term_id": "DOID:1040",
        "label": "chronic lymphocytic leukemia",
        "synonyms": ["CLL"],
        "source": "Human Disease Ontology",
    }
    candidate_short = _build_candidate("DOID:1036", 0.1, meta_short, None, "Human Disease Ontology")
    candidate_long = _build_candidate("DOID:1040", 0.1, meta_long, None, "Human Disease Ontology")

    thresholds = OntologyThresholds(min_confidence_to_accept=0.80, max_delta_for_ambiguity=0.05)
    result = choose_best_ontology_candidate("CLL", [candidate_short, candidate_long], thresholds)

    assert result.status == "MATCHED"
    assert result.match_type == "synonym_exact"
    assert result.best is not None
    assert result.best.term_id == "DOID:1040"
    assert result.confidence == 1.0


def test_synonym_exact_tie_break_uses_original_order_on_equal_specificity() -> None:
    meta_first = {
        "term_id": "TEST:0001",
        "label": "alpha zeta",
        "synonyms": ["CLL"],
        "source": "Human Disease Ontology",
    }
    meta_second = {
        "term_id": "TEST:0002",
        "label": "gamma beta",
        "synonyms": ["CLL"],
        "source": "Human Disease Ontology",
    }
    candidate_first = _build_candidate("TEST:0001", 0.1, meta_first, None, "Human Disease Ontology")
    candidate_second = _build_candidate("TEST:0002", 0.1, meta_second, None, "Human Disease Ontology")

    thresholds = OntologyThresholds(min_confidence_to_accept=0.80, max_delta_for_ambiguity=0.05)
    result = choose_best_ontology_candidate("CLL", [candidate_first, candidate_second], thresholds)

    assert result.status == "MATCHED"
    assert result.match_type == "synonym_exact"
    assert result.best is not None
    assert result.best.term_id == "TEST:0001"
    assert result.confidence == 1.0
