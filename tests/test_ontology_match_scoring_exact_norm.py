from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rag import ontology_retrieve
from validator.ontology_match import OntologyThresholds, choose_best_ontology_candidate


class FakeCollection:
    def __init__(self, entries) -> None:
        self.entries = entries

    def get(self, **kwargs):
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
                if _matches_where(meta, where):
                    results.append(entry)
        if limit is not None:
            results = results[:limit]
        return {
            "ids": [entry["id"] for entry in results],
            "metadatas": [entry.get("meta") for entry in results],
            "documents": [entry.get("doc") for entry in results],
        }

    def query(self, **kwargs):
        raise AssertionError("Vector fallback should not be called.")


def _matches_where(meta, where) -> bool:
    if not where:
        return True
    if "$and" in where:
        return all(_matches_where(meta, clause) for clause in where["$and"])
    if "$or" in where:
        return any(_matches_where(meta, clause) for clause in where["$or"])
    for key, value in where.items():
        if meta.get(key) != value:
            return False
    return True


def test_exact_norm_match_scoring(monkeypatch, tmp_path: Path) -> None:
    entries = [
        {
            "id": "CVCL:J703",
            "meta": {
                "term_id": "CVCL:J703",
                "label": "Myc-CaP",
                "source": "Cellosaurus",
                "label_norm": "myc-cap",
                "label_norm_compact": "myccap",
                "label_norm_space": "myc cap",
                "cell_line": "myc-cap",
                "cell_line_compact": "myccap",
                "cell_line_space": "myc cap",
            },
            "doc": "Myc-CaP",
        },
    ]
    collection = FakeCollection(entries)
    monkeypatch.setattr(
        ontology_retrieve,
        "get_chroma_collection",
        lambda *args, **kwargs: collection,
    )

    persist_path = tmp_path / "ontology_chroma_db"
    persist_path.mkdir()
    (persist_path / "chroma.sqlite3").touch()

    candidates = ontology_retrieve.retrieve_ontology_candidates(
        query="Myccap",
        source="Cellosaurus",
        persist_path=str(persist_path),
        collection_name="ontology_rag",
        embedding_model_name="unused",
        normalize_embeddings=True,
        top_k=5,
    )

    thresholds = OntologyThresholds(min_confidence_to_accept=0.80, max_delta_for_ambiguity=0.05)
    result = choose_best_ontology_candidate("Myccap", candidates, thresholds)

    assert result.status == "MATCHED"
    assert result.match_type == "label_norm_exact"
    assert result.confidence == 1.0
    assert result.best is not None
    assert result.best.term_id == "CVCL:J703"
    assert result.best.label == "Myc-CaP"
