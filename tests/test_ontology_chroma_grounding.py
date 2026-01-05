from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rag.ontology_retrieve import OntologyCandidate, retrieve_ontology_candidates
from validator.grounders import ontology_grounder
from validator.grounders import tissue_type as tissue_grounder
from validator.ontology_match import OntologyThresholds, choose_best_ontology_candidate


def _config() -> dict:
    return {
        "persist_path": "ontology_chroma_db",
        "collection_name": "ontology_rag",
        "k": 5,
        "ontology": {
            "enabled": True,
            "embedding": {
                "provider": "langchain_huggingface",
                "model_name": "BAAI/bge-base-en-v1.5",
                "normalize_embeddings": True,
            },
            "sources_by_field": {
                "tissue_type": "Uberon Ontology",
            },
            "thresholds": {
                "min_confidence_to_accept": 0.80,
                "max_delta_for_ambiguity": 0.05,
            },
        },
    }


def _candidate(term_id: str, label: str, synonyms: list[str] | None = None) -> OntologyCandidate:
    return OntologyCandidate(
        term_id=term_id,
        label=label,
        source="Uberon Ontology",
        definition=None,
        synonyms=synonyms or [],
        ancestors=[],
        distance=0.1,
        doc_text=None,
    )


def test_exact_label_match(monkeypatch) -> None:
    candidates = [_candidate("UBERON:0001", "heart")]
    monkeypatch.setattr(
        ontology_grounder,
        "retrieve_ontology_candidates",
        lambda *args, **kwargs: candidates,
    )
    match = tissue_grounder.ground_tissue_type("Heart", "", _config())
    assert match.status == "MATCHED"
    assert match.matched_term_id == "UBERON:0001"
    assert match.score == 1.0


def test_synonym_match(monkeypatch) -> None:
    candidates = [_candidate("UBERON:0002", "myocardium", ["heart"])]
    monkeypatch.setattr(
        ontology_grounder,
        "retrieve_ontology_candidates",
        lambda *args, **kwargs: candidates,
    )
    match = tissue_grounder.ground_tissue_type("Heart", "", _config())
    assert match.status == "MATCHED"
    assert match.matched_term_id == "UBERON:0002"
    assert match.score == 1.0
    assert match.match_type == "synonym_exact"
    assert match.matched_via == "synonym"


def test_close_tie_ambiguous(monkeypatch) -> None:
    candidates = [
        _candidate("UBERON:0003", "lung"),
        _candidate("UBERON:0004", "lung tissue", ["lung"]),
    ]
    monkeypatch.setattr(
        ontology_grounder,
        "retrieve_ontology_candidates",
        lambda *args, **kwargs: candidates,
    )
    match = tissue_grounder.ground_tissue_type("lung", "", _config())
    assert match.status == "AMBIGUOUS"
    assert match.matched_term_id is None


def test_low_similarity_low_confidence(monkeypatch) -> None:
    candidates = [_candidate("UBERON:0005", "heart")]
    monkeypatch.setattr(
        ontology_grounder,
        "retrieve_ontology_candidates",
        lambda *args, **kwargs: candidates,
    )
    match = tissue_grounder.ground_tissue_type("banana", "", _config())
    assert match.status == "LOW_CONFIDENCE"


def test_empty_candidates_no_match(monkeypatch) -> None:
    monkeypatch.setattr(
        ontology_grounder,
        "retrieve_ontology_candidates",
        lambda *args, **kwargs: [],
    )
    match = tissue_grounder.ground_tissue_type("Heart", "", _config())
    assert match.status == "NO_MATCH"


@pytest.mark.skipif(
    not os.getenv("ONTOLOGY_DB_PATH"),
    reason="Set ONTOLOGY_DB_PATH to run integration retrieval test.",
)
def test_retrieve_integration() -> None:
    db_path = os.environ["ONTOLOGY_DB_PATH"]
    if not os.path.isdir(db_path):
        pytest.skip("ONTOLOGY_DB_PATH does not point to a directory.")
    candidates = retrieve_ontology_candidates(
        query="PBMC",
        source="Cell Ontology",
        persist_path=db_path,
        collection_name="ontology_rag",
        embedding_model_name="BAAI/bge-base-en-v1.5",
        normalize_embeddings=True,
        top_k=5,
    )
    assert candidates

    thresholds = OntologyThresholds(min_confidence_to_accept=0.80, max_delta_for_ambiguity=0.05)
    result = choose_best_ontology_candidate("PBMC", candidates, thresholds)
    assert result.status in {"MATCHED", "AMBIGUOUS", "LOW_CONFIDENCE"}
