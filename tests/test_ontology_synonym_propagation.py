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
