from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import chromadb

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from validator.grounders import tissue_type as tissue_grounder


def test_runtime_query_uses_manual_embeddings(monkeypatch, tmp_path: Path) -> None:
    class DummyEmbeddingFunction:
        def __init__(self, model_name: str, device: str) -> None:
            self.model_name = model_name
            self.device = device

    persist_path = tmp_path / "ontology_chroma_db"
    persist_path.mkdir()
    sqlite_path = persist_path / "chroma.sqlite3"
    sqlite3.connect(sqlite_path).close()

    class FakeCollection:
        def get(self, **kwargs):
            return {"ids": [], "metadatas": [], "documents": []}

        def query(self, *, query_texts, n_results, where, include):
            assert query_texts == ["heart"]
            assert where == {"source": "Uberon Ontology"}
            return {
                "ids": [["UBERON:0001"]],
                "distances": [[0.1]],
                "metadatas": [[{
                    "term_id": "UBERON:0001",
                    "label": "heart",
                    "source": "Uberon Ontology",
                    "synonyms": ["cardiac"],
                    "definition": None,
                    "ancestors": [],
                }]],
                "documents": [["Assay: assay"]],
            }

    fake_collection = FakeCollection()

    class FakeClient:
        def get_collection(self, name, **kwargs):
            embedding_function = kwargs.get("embedding_function")
            assert isinstance(embedding_function, DummyEmbeddingFunction)
            assert embedding_function.device == "cpu"
            assert name == "ontology_rag"
            return fake_collection

    monkeypatch.setattr(
        chromadb.utils.embedding_functions,
        "SentenceTransformerEmbeddingFunction",
        DummyEmbeddingFunction,
        raising=True,
    )

    monkeypatch.setattr(
        chromadb,
        "PersistentClient",
        lambda *args, **kwargs: FakeClient(),
        raising=True,
    )

    config = {
        "persist_path": str(persist_path),
        "collection_name": "ontology_rag",
        "k": 5,
        "ontology": {
            "enabled": True,
            "embedding": {
                "provider": "langchain_huggingface",
                "model_name": "BAAI/bge-base-en-v1.5",
                "normalize_embeddings": True,
            },
            "sources_by_field": {"tissue_type": "Uberon Ontology"},
            "thresholds": {
                "min_confidence_to_accept": 0.80,
                "max_delta_for_ambiguity": 0.05,
            },
        },
    }

    match = tissue_grounder.ground_tissue_type("heart", "", config)
    assert match.status == "MATCHED"
    assert match.matched_term_id == "UBERON:0001"
