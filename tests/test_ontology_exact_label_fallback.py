from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rag import ontology_retrieve
from validator.ontology_match import OntologyThresholds, choose_best_ontology_candidate


def test_exact_label_lookup_fallback(monkeypatch, tmp_path: Path) -> None:
    persist_path = tmp_path / "ontology_chroma_db"
    persist_path.mkdir()
    (persist_path / "chroma.sqlite3").touch()

    class FakeCollection:
        def query(self, **kwargs):
            raise AssertionError("Vector fallback should not be called.")

        def get(self, **kwargs):
            assert kwargs["where"] == {
                "$and": [
                    {"source": "Experimental Factor Ontology"},
                    {
                        "$or": [
                            {"label_norm": "atac-seq"},
                            {"label_norm_compact": "atacseq"},
                            {"label_norm_space": "atac seq"},
                            {"data_type": "atac-seq"},
                            {"data_type_compact": "atacseq"},
                            {"data_type_space": "atac seq"},
                        ]
                    },
                ]
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

    monkeypatch.setattr(
        ontology_retrieve,
        "get_chroma_collection",
        lambda *args, **kwargs: fake_collection,
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
    assert result.match_type == "label_norm_exact"
    assert result.best is not None
    assert result.best.term_id == "EFO:0007045"
    assert result.confidence == 1.0
