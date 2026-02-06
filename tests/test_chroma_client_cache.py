from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import chromadb

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rag import chroma_client
from rag.ontology_retrieve import retrieve_ontology_candidates


def test_chroma_client_and_collection_reused_across_grounding_calls(
    monkeypatch,
    tmp_path: Path,
) -> None:
    persist_path = tmp_path / "ontology_chroma_db"
    persist_path.mkdir()
    sqlite3.connect(persist_path / "chroma.sqlite3").close()

    counts = {"client_init": 0, "collection_open": 0}

    class FakeCollection:
        def get(self, **kwargs):
            return {
                "ids": [["UBERON:0001"]],
                "metadatas": [[
                    {
                        "term_id": "UBERON:0001",
                        "label": "heart",
                        "source": "Uberon Ontology",
                        "synonyms": [],
                        "definition": None,
                        "ancestors": [],
                    }
                ]],
                "documents": [["heart"]],
            }

        def query(self, **kwargs):
            raise AssertionError("vector query should not run for exact metadata match")

    fake_collection = FakeCollection()

    class FakeClient:
        def get_collection(self, name, **kwargs):
            assert name == "ontology_rag"
            counts["collection_open"] += 1
            return fake_collection

    def _fake_persistent_client(*, path, settings=None):
        assert settings is None
        assert path == str(persist_path)
        counts["client_init"] += 1
        return FakeClient()

    monkeypatch.setattr(
        chromadb,
        "PersistentClient",
        _fake_persistent_client,
        raising=True,
    )

    chroma_client.reset_chroma_client_cache()
    first = retrieve_ontology_candidates(
        query="heart",
        source="Uberon Ontology",
        persist_path=str(persist_path),
        collection_name="ontology_rag",
        embedding_model_name="BAAI/bge-base-en-v1.5",
        normalize_embeddings=True,
        embedding_device="cpu",
        top_k=5,
    )
    second = retrieve_ontology_candidates(
        query="heart",
        source="Uberon Ontology",
        persist_path=str(persist_path),
        collection_name="ontology_rag",
        embedding_model_name="BAAI/bge-base-en-v1.5",
        normalize_embeddings=True,
        embedding_device="cpu",
        top_k=5,
    )

    assert len(first) == 1
    assert len(second) == 1
    assert counts["client_init"] == 1
    assert counts["collection_open"] == 1


def test_chroma_cache_key_includes_client_settings(monkeypatch, tmp_path: Path) -> None:
    persist_path = tmp_path / "ontology_chroma_db"
    persist_path.mkdir()

    counts = {"client_init": 0}

    class FakeClient:
        def get_collection(self, name, **kwargs):
            return {"name": name}

        def get_or_create_collection(self, name, **kwargs):
            return {"name": name, "created": True}

    def _fake_persistent_client(*, path, settings=None):
        assert path == str(persist_path)
        counts["client_init"] += 1
        return FakeClient()

    monkeypatch.setattr(
        chromadb,
        "PersistentClient",
        _fake_persistent_client,
        raising=True,
    )

    chroma_client.reset_chroma_client_cache()
    client_a = chroma_client.get_chroma_client(
        str(persist_path),
        client_settings={"tenant": "A", "database": "db"},
    )
    client_a_reordered = chroma_client.get_chroma_client(
        str(persist_path),
        client_settings={"database": "db", "tenant": "A"},
    )
    client_b = chroma_client.get_chroma_client(
        str(persist_path),
        client_settings={"tenant": "B", "database": "db"},
    )

    assert client_a is client_a_reordered
    assert client_a is not client_b
    assert counts["client_init"] == 2
