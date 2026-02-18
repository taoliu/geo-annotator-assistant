from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rag import ontology_retrieve


class FakeCollection:
    def __init__(self, entries, vector_results=None, raise_on_query=False) -> None:
        self.entries = entries
        self.vector_results = vector_results or []
        self.raise_on_query = raise_on_query
        self.query_calls = 0
        self.get_calls = []

    def _matches_where(self, meta, where) -> bool:
        if not where:
            return True
        if "$and" in where:
            return all(self._matches_where(meta, clause) for clause in where["$and"])
        if "$or" in where:
            return any(self._matches_where(meta, clause) for clause in where["$or"])
        for key, value in where.items():
            if meta.get(key) != value:
                return False
        return True

    def get(self, **kwargs):
        self.get_calls.append(kwargs)
        ids = kwargs.get("ids")
        where = kwargs.get("where")
        limit = kwargs.get("limit")
        results = []
        if ids is not None:
            id_set = set(ids)
            for entry in self.entries:
                if entry["id"] in id_set:
                    results.append(entry)
        else:
            for entry in self.entries:
                meta = entry.get("meta") or {}
                if self._matches_where(meta, where):
                    results.append(entry)
        if limit is not None:
            results = results[:limit]
        return {
            "ids": [entry["id"] for entry in results],
            "metadatas": [entry.get("meta") for entry in results],
            "documents": [entry.get("doc") for entry in results],
        }

    def query(self, **kwargs):
        self.query_calls += 1
        if self.raise_on_query:
            raise AssertionError("Vector fallback should not be called.")
        where = kwargs.get("where")
        results = []
        for entry in self.vector_results:
            meta = entry.get("meta") or {}
            if where and not self._matches_where(meta, where):
                continue
            results.append(entry)
        return {
            "ids": [[entry["id"] for entry in results]],
            "distances": [[entry.get("dist", 0.4) for entry in results]],
            "metadatas": [[entry.get("meta") for entry in results]],
            "documents": [[entry.get("doc") for entry in results]],
        }


def _persist_path(tmp_path: Path) -> Path:
    persist_path = tmp_path / "ontology_chroma_db"
    persist_path.mkdir()
    (persist_path / "chroma.sqlite3").touch()
    return persist_path


def test_exact_metadata_match_label_norm(monkeypatch, tmp_path: Path) -> None:
    entries = [
        {
            "id": "CVCL_1234",
            "meta": {
                "term_id": "CVCL_1234",
                "label": "Myc-CaP",
                "source": "Cellosaurus",
                "label_norm": "myc-cap",
                "label_norm_compact": "myccap",
                "label_norm_space": "myc cap",
            },
            "doc": "Myc-CaP",
        },
    ]
    collection = FakeCollection(entries, raise_on_query=True)
    monkeypatch.setattr(
        ontology_retrieve,
        "get_chroma_collection",
        lambda *args, **kwargs: collection,
    )

    candidates = ontology_retrieve.retrieve_ontology_candidates(
        query="Myc-CaP",
        source="Cellosaurus",
        persist_path=str(_persist_path(tmp_path)),
        collection_name="ontology_rag",
        embedding_model_name="unused",
        normalize_embeddings=True,
        top_k=5,
    )

    assert candidates
    assert candidates[0].retrieval_mode == "meta_exact"
    assert candidates[0].distance == 0.0
    assert candidates[0].term_id == "CVCL_1234"
    assert candidates[0].label == "Myc-CaP"
    assert candidates[0].source == "Cellosaurus"
    assert candidates[0].query_candidate == "Myc-CaP"


def test_source_specific_fields_match(monkeypatch, tmp_path: Path) -> None:
    entries = [
        {
            "id": "CVCL_0001",
            "meta": {
                "term_id": "CVCL_0001",
                "label": "Myc-CaP",
                "source": "Cellosaurus",
                "cell_line": "myc-cap",
                "cell_line_compact": "myccap",
                "cell_line_space": "myc cap",
            },
            "doc": "Myc-CaP",
        },
    ]
    collection = FakeCollection(entries, raise_on_query=True)
    monkeypatch.setattr(
        ontology_retrieve,
        "get_chroma_collection",
        lambda *args, **kwargs: collection,
    )

    candidates = ontology_retrieve.retrieve_ontology_candidates(
        query="Myc-CaP",
        source="Cellosaurus",
        persist_path=str(_persist_path(tmp_path)),
        collection_name="ontology_rag",
        embedding_model_name="unused",
        normalize_embeddings=True,
        top_k=5,
    )

    assert candidates
    assert candidates[0].retrieval_mode == "meta_exact"
    assert candidates[0].term_id == "CVCL_0001"


def test_id_get_fast_path(monkeypatch, tmp_path: Path) -> None:
    entries = [
        {
            "id": "CVCL:J703",
            "meta": {
                "term_id": "CVCL:J703",
                "label": "Myc-CaP",
                "source": "Cellosaurus",
            },
            "doc": "Myc-CaP",
        },
    ]
    collection = FakeCollection(entries, raise_on_query=True)
    monkeypatch.setattr(
        ontology_retrieve,
        "get_chroma_collection",
        lambda *args, **kwargs: collection,
    )

    candidates = ontology_retrieve.retrieve_ontology_candidates(
        query="CVCL:J703",
        source="Cellosaurus",
        persist_path=str(_persist_path(tmp_path)),
        collection_name="ontology_rag",
        embedding_model_name="unused",
        normalize_embeddings=True,
        top_k=5,
    )

    assert candidates
    assert candidates[0].retrieval_mode == "id_get"
    assert candidates[0].term_id == "CVCL:J703"
    assert candidates[0].query_candidate == "CVCL:J703"
    assert collection.query_calls == 0


def test_vector_fallback(monkeypatch, tmp_path: Path) -> None:
    vector_results = [
        {
            "id": "CVCL_9999",
            "meta": {
                "term_id": "CVCL_9999",
                "label": "Fallback line",
                "source": "Cellosaurus",
            },
            "doc": "Fallback line",
            "dist": 0.33,
        },
    ]
    collection = FakeCollection(entries=[], vector_results=vector_results)
    monkeypatch.setattr(
        ontology_retrieve,
        "get_chroma_collection",
        lambda *args, **kwargs: collection,
    )
    def fake_build_embedding_function(*args, **kwargs):
        class DummyEmbeddingFunction:
            def __call__(self, texts):
                return [[0.0, 0.0, 0.0] for _ in texts]

        return DummyEmbeddingFunction()

    monkeypatch.setattr(
        ontology_retrieve,
        "build_embedding_function",
        fake_build_embedding_function,
        raising=True,
    )

    candidates = ontology_retrieve.retrieve_ontology_candidates(
        query="Unknown",
        source="Cellosaurus",
        persist_path=str(_persist_path(tmp_path)),
        collection_name="ontology_rag",
        embedding_model_name="unused",
        normalize_embeddings=True,
        top_k=5,
    )

    assert candidates
    assert candidates[0].retrieval_mode == "vector_fallback"
    assert candidates[0].distance == 0.33
    assert candidates[0].term_id == "CVCL_9999"


def test_candidate_extraction_no_token_splitting() -> None:
    candidates = ontology_retrieve.extract_candidates("Myc-CaP")
    assert "Myc-CaP" in candidates
    assert "myc" not in candidates
    assert "cap" not in candidates


def test_lookup_exact_synonym_ids_parses_json_string_and_normalizes(tmp_path: Path) -> None:
    sqlite_path = tmp_path / "chroma.sqlite3"
    with sqlite3.connect(sqlite_path) as conn:
        conn.executescript(
            """
            CREATE TABLE embeddings (
                id INTEGER PRIMARY KEY,
                segment_id TEXT NOT NULL,
                embedding_id TEXT NOT NULL,
                seq_id BLOB NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (segment_id, embedding_id)
            );
            CREATE TABLE embedding_metadata (
                id INTEGER,
                key TEXT NOT NULL,
                string_value TEXT,
                int_value INTEGER,
                float_value REAL,
                bool_value INTEGER,
                PRIMARY KEY (id, key)
            );
            """
        )
        conn.execute(
            "INSERT INTO embeddings (id, segment_id, embedding_id, seq_id) VALUES (1, ?, ?, ?)",
            ("seg", "NCIT:C4913", b"\x01"),
        )
        conn.execute(
            "INSERT INTO embeddings (id, segment_id, embedding_id, seq_id) VALUES (2, ?, ?, ?)",
            ("seg", "NCIT:C7000", b"\x02"),
        )
        conn.execute(
            "INSERT INTO embedding_metadata (id, key, string_value) VALUES (1, 'source', 'NCI Thesaurus')"
        )
        conn.execute(
            "INSERT INTO embedding_metadata (id, key, string_value) VALUES (1, 'synonyms', ?)",
            ('["Malignant Female Reproductive System Tumor", "gynecologic cancer"]',),
        )
        conn.execute(
            "INSERT INTO embedding_metadata (id, key, string_value) VALUES (2, 'source', 'NCI Thesaurus')"
        )
        conn.execute(
            "INSERT INTO embedding_metadata (id, key, string_value) VALUES (2, 'synonyms', ?)",
            ('["B-Cell Malignancy"]',),
        )

    gynecologic_ids = ontology_retrieve._lookup_exact_synonym_ids(
        str(sqlite_path),
        "NCI Thesaurus",
        "Gynecologic cancer",
    )
    assert gynecologic_ids == ["NCIT:C4913"]

    malignancy_ids = ontology_retrieve._lookup_exact_synonym_ids(
        str(sqlite_path),
        "NCI Thesaurus",
        "B cell malignancies",
    )
    assert malignancy_ids == ["NCIT:C7000"]


def test_ncit_synonym_exact_ids_short_circuit_vector(monkeypatch, tmp_path: Path) -> None:
    entries = [
        {
            "id": "NCIT:C4913",
            "meta": {
                "term_id": "NCIT:C4913",
                "label": "Malignant Female Reproductive System Neoplasm",
                "source": "NCI Thesaurus",
                "synonyms": '["gynecologic cancer"]',
            },
            "doc": "Cancer Type: Malignant Female Reproductive System Neoplasm",
        },
    ]
    collection = FakeCollection(entries, raise_on_query=True)
    monkeypatch.setattr(
        ontology_retrieve,
        "get_chroma_collection",
        lambda *args, **kwargs: collection,
    )
    monkeypatch.setattr(
        ontology_retrieve,
        "_lookup_exact_synonym_ids",
        lambda *args, **kwargs: ["NCIT:C4913"],
    )

    candidates = ontology_retrieve.retrieve_ontology_candidates(
        query="Gynecologic cancer",
        source="NCI Thesaurus",
        persist_path=str(_persist_path(tmp_path)),
        collection_name="ontology_rag",
        embedding_model_name="unused",
        normalize_embeddings=True,
        top_k=5,
    )

    assert candidates
    assert candidates[0].term_id == "NCIT:C4913"
    assert candidates[0].retrieval_mode == "synonym_exact_get"
    assert collection.query_calls == 0
