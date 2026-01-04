from __future__ import annotations

import sqlite3
import sys
import types
from pathlib import Path

import chromadb

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from validator.grounders import tissue_type as tissue_grounder


def test_runtime_query_uses_manual_embeddings(monkeypatch, tmp_path: Path) -> None:
    class DummyEmbeddings:
        def __init__(self, model_name: str, encode_kwargs: dict) -> None:
            self.model_name = model_name
            self.encode_kwargs = encode_kwargs

        def embed_query(self, text: str) -> list[float]:
            return [0.1, 0.2, 0.3]

    dummy_module = types.ModuleType("langchain_huggingface")
    dummy_module.HuggingFaceEmbeddings = DummyEmbeddings
    monkeypatch.setitem(sys.modules, "langchain_huggingface", dummy_module)

    persist_path = tmp_path / "ontology_chroma_db"
    persist_path.mkdir()
    sqlite_path = persist_path / "chroma.sqlite3"
    sqlite3.connect(sqlite_path).close()

    class FakeCollection:
        def query(self, *, query_embeddings, n_results, where, include):
            assert query_embeddings == [[0.1, 0.2, 0.3]]
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
            assert "embedding_function" not in kwargs
            assert name == "ontology_rag"
            return fake_collection

    monkeypatch.setattr(
        chromadb,
        "PersistentClient",
        lambda *args, **kwargs: FakeClient(),
        raising=True,
    )

    config = {
        "ontology_chroma_enabled": True,
        "ontology_chroma_db_path": str(persist_path),
        "ontology_chroma_collection": "ontology_rag",
        "ontology_embedding_model_name": "BAAI/bge-base-en-v1.5",
        "ontology_embedding_normalize": True,
        "ontology_top_k": 5,
        "ontology_sources_by_field": {"tissue_type": "Uberon Ontology"},
        "ontology_thresholds": {
            "min_confidence_to_accept": 0.80,
            "max_delta_for_ambiguity": 0.05,
        },
    }

    match = tissue_grounder.ground_tissue_type("heart", "", config)
    assert match.status == "MATCHED"
    assert match.matched_term_id == "UBERON:0001"
