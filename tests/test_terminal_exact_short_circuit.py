from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rag import ontology_retrieve
from validator.grounders import ontology_grounder
from validator.grounders import tissue_type as tissue_grounder
from rag.ontology_retrieve import OntologyCandidate


def _config(tmp_path: Path) -> dict:
    persist_path = tmp_path / "ontology_chroma_db"
    persist_path.mkdir()
    (persist_path / "chroma.sqlite3").touch()
    return {
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


def test_terminal_exact_skips_vector_query(monkeypatch, tmp_path: Path) -> None:
    class FakeCollection:
        def get(self, **kwargs):
            return {
                "ids": ["UBERON:0001"],
                "metadatas": [
                    {
                        "term_id": "UBERON:0001",
                        "label": "Myc-CaP",
                        "source": "Uberon Ontology",
                        "label_norm": "myc-cap",
                        "label_norm_compact": "myccap",
                        "label_norm_space": "myc cap",
                    }
                ],
                "documents": ["Myc-CaP"],
            }

        def query(self, **kwargs):
            raise AssertionError("Vector fallback should not be called.")

    monkeypatch.setattr(
        ontology_retrieve,
        "get_chroma_collection",
        lambda *args, **kwargs: FakeCollection(),
    )

    match = tissue_grounder.ground_tissue_type("Myc-CaP", "", _config(tmp_path))
    assert match.status == "MATCHED"
    assert match.match_type == "label_norm_exact"
    assert match.vector_fallback_skipped is True
    assert match.alternates and match.alternates[0]["term_id"] == "UBERON:0001"


def test_terminal_exact_skips_embedding_calls(monkeypatch, tmp_path: Path) -> None:
    class FakeCollection:
        def get(self, **kwargs):
            return {
                "ids": ["UBERON:0002"],
                "metadatas": [
                    {
                        "term_id": "UBERON:0002",
                        "label": "Heart",
                        "source": "Uberon Ontology",
                        "label_norm": "heart",
                        "label_norm_compact": "heart",
                        "label_norm_space": "heart",
                    }
                ],
                "documents": ["Heart"],
            }

        def query(self, **kwargs):
            raise AssertionError("Vector fallback should not be called.")

    calls = {"build": 0, "embed": 0}

    def fake_build_embedding_function(*args, **kwargs):
        calls["build"] += 1

        class DummyEmbeddingFunction:
            def __call__(self, texts):
                calls["embed"] += len(list(texts))
                return [[0.0, 0.0, 0.0] for _ in texts]

        return DummyEmbeddingFunction()

    monkeypatch.setattr(
        ontology_retrieve,
        "get_chroma_collection",
        lambda *args, **kwargs: FakeCollection(),
    )
    monkeypatch.setattr(
        ontology_retrieve,
        "build_embedding_function",
        fake_build_embedding_function,
        raising=True,
    )

    match = tissue_grounder.ground_tissue_type("Heart", "", _config(tmp_path))
    assert match.status == "MATCHED"
    assert match.vector_fallback_skipped is True
    assert calls["build"] == 0
    assert calls["embed"] == 0


def test_synonym_exact_short_circuit(monkeypatch, tmp_path: Path) -> None:
    candidates = [
        OntologyCandidate(
            term_id="UBERON:0003",
            label="myocardium",
            source="Uberon Ontology",
            definition=None,
            synonyms=["heart"],
            ancestors=[],
            distance=0.1,
            doc_text=None,
        )
    ]

    monkeypatch.setattr(
        ontology_grounder,
        "retrieve_ontology_candidates",
        lambda *args, **kwargs: candidates,
    )

    match = tissue_grounder.ground_tissue_type("heart", "", _config(tmp_path))
    assert match.status == "MATCHED"
    assert match.match_type == "synonym_exact"
    assert match.vector_fallback_skipped is True
    assert len(match.alternates) == 1
    assert match.alternates[0]["term_id"] == "UBERON:0003"


def test_non_terminal_allows_vector_fallback(monkeypatch, tmp_path: Path) -> None:
    class FakeCollection:
        def __init__(self) -> None:
            self.query_calls = 0

        def get(self, **kwargs):
            return {"ids": [], "metadatas": [], "documents": []}

        def query(self, *, query_embeddings, n_results, where, include=None):
            self.query_calls += 1
            assert query_embeddings == [[0.0, 0.0, 0.0]]
            return {
                "ids": [["UBERON:9999"]],
                "distances": [[0.9]],
                "metadatas": [[{
                    "term_id": "UBERON:9999",
                    "label": "apple",
                    "source": "Uberon Ontology",
                    "synonyms": [],
                    "definition": None,
                    "ancestors": [],
                }]],
                "documents": [["apple"]],
            }

    collection = FakeCollection()

    def fake_build_embedding_function(*args, **kwargs):
        class DummyEmbeddingFunction:
            def __call__(self, texts):
                return [[0.0, 0.0, 0.0] for _ in texts]

        return DummyEmbeddingFunction()

    monkeypatch.setattr(
        ontology_retrieve,
        "get_chroma_collection",
        lambda *args, **kwargs: collection,
    )
    monkeypatch.setattr(
        ontology_retrieve,
        "build_embedding_function",
        fake_build_embedding_function,
        raising=True,
    )

    match = tissue_grounder.ground_tissue_type("banana", "", _config(tmp_path))
    assert match.status in {"LOW_CONFIDENCE", "AMBIGUOUS", "NO_MATCH", "MATCHED"}
    assert collection.query_calls == 1
