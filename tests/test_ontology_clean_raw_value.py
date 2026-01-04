from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rag.ontology_retrieve import OntologyCandidate
from validator.ontology_match import (
    OntologyThresholds,
    clean_raw_value_for_ontology,
    choose_best_ontology_candidate,
)


def test_clean_raw_value_colon_prefixes() -> None:
    assert clean_raw_value_for_ontology("tissue: liver") == "liver"
    assert clean_raw_value_for_ontology("disease: HIV-1") == "HIV-1"
    assert clean_raw_value_for_ontology("cell line: K562") == "K562"


def test_clean_raw_value_no_change() -> None:
    assert clean_raw_value_for_ontology("liver") == "liver"


def test_clean_raw_value_spacing() -> None:
    assert clean_raw_value_for_ontology("tissue:liver") == "liver"
    assert clean_raw_value_for_ontology("tissue:  liver ") == "liver"


def test_clean_raw_value_optional_separators() -> None:
    assert clean_raw_value_for_ontology("tissue = liver") == "liver"
    assert clean_raw_value_for_ontology("tissue - liver") == "liver"


def test_cleaning_improves_selection_confidence() -> None:
    candidates = [
        OntologyCandidate(
            term_id="UBERON:0002107",
            label="liver",
            source="Uberon Ontology",
            definition=None,
            synonyms=[],
            ancestors=[],
            distance=0.1,
            doc_text=None,
        ),
        OntologyCandidate(
            term_id="UBERON:0000479",
            label="tissue",
            source="Uberon Ontology",
            definition=None,
            synonyms=[],
            ancestors=[],
            distance=0.2,
            doc_text=None,
        ),
    ]
    thresholds = OntologyThresholds(min_confidence_to_accept=0.80, max_delta_for_ambiguity=0.05)
    result = choose_best_ontology_candidate("tissue: liver", candidates, thresholds)
    assert result.status == "MATCHED"
    assert result.best is not None
    assert result.best.term_id == "UBERON:0002107"
    assert result.best.confidence == 1.0
