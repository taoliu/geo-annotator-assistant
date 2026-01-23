from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from validator.failure_codes import (
    ONTOLOGY_LOW_CONFIDENCE_DATA_TYPE,
    ONTOLOGY_NO_MATCH_DATA_TYPE,
)
from validator.ontology_match import OntologyMatch
from validator.ontology_validator import ground_all_fields

import validator.grounders.data_type as data_type_grounder


def test_fallback_tissue_type_unknown_no_failures(monkeypatch) -> None:
    def dummy_ground_data_type(raw_value, context_text, config):
        return OntologyMatch(
            field="data_type",
            raw_value=raw_value,
            ontology="Experimental Factor Ontology",
            status="MATCHED",
            matched_term_id="EFO:0001234",
            matched_label="RNA-seq",
            matched_source="Experimental Factor Ontology",
            match_type="label_exact",
            score=0.9,
            alternates=[],
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
    matches, failures = ground_all_fields(llm_output, "", {})
    assert failures == {}
    assert matches["tissue_type"].status == "FALLBACK"


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
    _, failures = ground_all_fields(llm_output, "", {})
    assert failures == {"data_type": ONTOLOGY_NO_MATCH_DATA_TYPE}


def test_low_confidence_grounder(monkeypatch) -> None:
    def low_confidence_grounder(raw_value, context_text, config):
        return OntologyMatch(
            field="data_type",
            raw_value=raw_value,
            ontology="Experimental Factor Ontology",
            status="LOW_CONFIDENCE",
            matched_term_id=None,
            matched_label=None,
            matched_source=None,
            match_type="jaccard",
            score=0.4,
            alternates=[],
        )

    monkeypatch.setattr(
        data_type_grounder,
        "ground_data_type",
        low_confidence_grounder,
        raising=False,
    )

    llm_output = {
        "data_type": "RNA-seq",
        "tissue_type": "Unknown",
        "cell_line": "No",
        "disease": "Healthy",
    }
    _, failures = ground_all_fields(llm_output, "", {})
    assert failures == {"data_type": ONTOLOGY_LOW_CONFIDENCE_DATA_TYPE}


def test_microarray_allowlist_enabled_short_circuits_grounder(monkeypatch) -> None:
    called = {"value": False}

    def dummy_ground_data_type(raw_value, context_text, config):
        called["value"] = True
        return OntologyMatch(
            field="data_type",
            raw_value=raw_value,
            ontology="Experimental Factor Ontology",
            status="NO_MATCH",
            matched_term_id=None,
            matched_label=None,
            matched_source=None,
            match_type="none",
            score=None,
            alternates=[],
        )

    monkeypatch.setattr(
        data_type_grounder,
        "ground_data_type",
        dummy_ground_data_type,
        raising=False,
    )

    llm_output = {
        "data_type": "Microarray",
        "tissue_type": "Unknown",
        "cell_line": "No",
        "disease": "Healthy",
    }
    config = {
        "ontology": {
            "data_type": {
                "fallback_allowlist_enabled": True,
                "fallback_allowlist": ["Microarray"],
            }
        }
    }
    matches, failures = ground_all_fields(llm_output, "", config)
    assert failures == {}
    assert matches["data_type"].status == "FALLBACK"
    assert matches["data_type"].match_type == "fallback"
    assert called["value"] is False


def test_microarray_allowlist_disabled_uses_grounder(monkeypatch) -> None:
    called = {"value": False}

    def dummy_ground_data_type(raw_value, context_text, config):
        called["value"] = True
        return OntologyMatch(
            field="data_type",
            raw_value=raw_value,
            ontology="Experimental Factor Ontology",
            status="NO_MATCH",
            matched_term_id=None,
            matched_label=None,
            matched_source=None,
            match_type="none",
            score=None,
            alternates=[],
        )

    monkeypatch.setattr(
        data_type_grounder,
        "ground_data_type",
        dummy_ground_data_type,
        raising=False,
    )

    llm_output = {
        "data_type": "Microarray",
        "tissue_type": "Unknown",
        "cell_line": "No",
        "disease": "Healthy",
    }
    config = {
        "ontology": {
            "data_type": {
                "fallback_allowlist_enabled": False,
                "fallback_allowlist": ["Microarray"],
            }
        }
    }
    matches, failures = ground_all_fields(llm_output, "", config)
    assert failures == {"data_type": ONTOLOGY_NO_MATCH_DATA_TYPE}
    assert matches["data_type"].status == "NO_MATCH"
    assert called["value"] is True
