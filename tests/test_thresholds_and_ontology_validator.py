from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from validator.ontology_match import OntologyMatch
from validator.ontology_validator import (
    ONTOLOGY_LOW_SCORE,
    ONTOLOGY_NO_MATCH,
    ground_all_fields,
)
from validator.thresholds import is_match_acceptable

import validator.grounders.data_type as data_type_grounder


def test_threshold_cell_line_match_ok() -> None:
    match = OntologyMatch(
        field="cell_line",
        raw_value="HeLa",
        ontology="CELLOSAURUS",
        matched_term_id="CVCL_0030",
        matched_label="HeLa",
        match_type="exact",
        score=0.8,
    )
    assert is_match_acceptable("cell_line", match) is True


def test_threshold_cell_line_match_low() -> None:
    match = OntologyMatch(
        field="cell_line",
        raw_value="HeLa",
        ontology="CELLOSAURUS",
        matched_term_id="CVCL_0030",
        matched_label="HeLa",
        match_type="exact",
        score=0.7,
    )
    assert is_match_acceptable("cell_line", match) is False


def test_fallback_tissue_type_unknown_no_failures(monkeypatch) -> None:
    def dummy_ground_data_type(raw_value, context_text, persist_path, collection_name, k):
        return OntologyMatch(
            field="data_type",
            raw_value=raw_value,
            ontology="EFO",
            matched_term_id="EFO:0001234",
            matched_label="RNA-seq",
            match_type="exact",
            score=0.9,
        )

    monkeypatch.setattr(
        data_type_grounder,
        "ground_data_type",
        dummy_ground_data_type,
        raising=False,
    )

    llm_output = {
        "data_type": "RNA-seq",
        "tissue_type": "Unknown",
        "cell_line": "No",
        "disease": "Healthy",
    }
    rag_config = {
        "persist_path": "/tmp",
        "collections": {"EFO": "efo"},
        "k": 10,
    }
    matches, failures = ground_all_fields(llm_output, "", rag_config)
    assert failures == {}
    assert matches["tissue_type"].match_type == "fallback"


def test_placeholder_grounder_no_match(monkeypatch) -> None:
    def placeholder_grounder(*args, **kwargs):
        raise NotImplementedError("stub")

    monkeypatch.setattr(
        data_type_grounder,
        "ground_data_type",
        placeholder_grounder,
        raising=False,
    )

    llm_output = {
        "data_type": "RNA-seq",
        "tissue_type": "Unknown",
        "cell_line": "No",
        "disease": "Healthy",
    }
    rag_config = {"persist_path": "/tmp", "collections": {"EFO": "efo"}}
    _, failures = ground_all_fields(llm_output, "", rag_config)
    assert failures == {"data_type": ONTOLOGY_NO_MATCH}


def test_low_score_grounder(monkeypatch) -> None:
    def low_score_grounder(raw_value, context_text, persist_path, collection_name, k):
        return OntologyMatch(
            field="data_type",
            raw_value=raw_value,
            ontology="EFO",
            matched_term_id="EFO:0001234",
            matched_label="RNA-seq",
            match_type="fuzzy",
            score=0.5,
        )

    monkeypatch.setattr(
        data_type_grounder,
        "ground_data_type",
        low_score_grounder,
        raising=False,
    )

    llm_output = {
        "data_type": "RNA-seq",
        "tissue_type": "Unknown",
        "cell_line": "No",
        "disease": "Healthy",
    }
    rag_config = {"persist_path": "/tmp", "collections": {"EFO": "efo"}}
    _, failures = ground_all_fields(llm_output, "", rag_config)
    assert failures == {"data_type": ONTOLOGY_LOW_SCORE}
