from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rag import ontology_retrieve
from validator.ontology_match import OntologyThresholds, choose_best_ontology_candidate


def test_exact_label_lookup_fallback(monkeypatch, tmp_path: Path) -> None:
    class DummyEmbeddings:
        def embed_query(self, text: str) -> list[float]:
            return [0.1, 0.2, 0.3]

    monkeypatch.setattr(
        ontology_retrieve,
        "_load_embedding_function",
        lambda model_name, normalize_embeddings: DummyEmbeddings(),
    )

    persist_path = tmp_path / "ontology_chroma_db"
    persist_path.mkdir()
    sqlite_path = persist_path / "chroma.sqlite3"
    sqlite3.connect(sqlite_path).close()

    class FakeCollection:
        def query(self, *, query_embeddings, n_results, where, include):
            return {
                "ids": [[]],
                "distances": [[]],
                "metadatas": [[]],
                "documents": [[]],
            }

        def get(self, *, where, include):
            assert where == {
                "source": "Experimental Factor Ontology",
                "label": "ATAC-seq",
            }
            return {
                "ids": ["EFO:0007045"],
                "metadatas": [
                    {
                        "term_id": "EFO:0007045",
                        "label": "ATAC-seq",
                        "source": "Experimental Factor Ontology",
                        "synonyms": [],
                        "definition": None,
                        "ancestors": [],
                    }
                ],
                "documents": ["ATAC-seq"],
            }

    fake_collection = FakeCollection()

    class FakeClient:
        def get_collection(self, name, **kwargs):
            assert name == "ontology_rag"
            return fake_collection

    monkeypatch.setattr(
        ontology_retrieve,
        "get_chroma_client",
        lambda path: FakeClient(),
        raising=True,
    )

    candidates = ontology_retrieve.retrieve_ontology_candidates(
        query="ATAC seq",
        source="Experimental Factor Ontology",
        persist_path=str(persist_path),
        collection_name="ontology_rag",
        embedding_model_name="dummy",
        normalize_embeddings=True,
        top_k=5,
    )

    result = choose_best_ontology_candidate(
        "ATAC-seq",
        candidates,
        OntologyThresholds(min_confidence_to_accept=0.80, max_delta_for_ambiguity=0.05),
    )

    assert result.status == "MATCHED"
    assert result.match_type == "label_exact"
    assert result.best is not None
    assert result.best.term_id == "EFO:0007045"
    assert result.confidence == 1.0
