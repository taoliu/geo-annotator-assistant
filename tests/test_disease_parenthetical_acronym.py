from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agent.config import load_config
from rag.ontology_retrieve import OntologyCandidate
from validator.grounders import disease as disease_grounder


def _base_rag_config() -> dict:
    cfg = load_config(str(ROOT / "config" / "example_config.yaml"))
    rag_cfg = cfg.get("rag") or {}
    rag_cfg.setdefault("ontology", {})["enabled"] = True
    rag_cfg["ontology"].setdefault("disease", {})
    rag_cfg["ontology"]["disease"].setdefault("ncit_fallback", {})
    rag_cfg["ontology"]["disease"]["ncit_fallback"]["enabled"] = True
    rag_cfg["ontology"]["disease"]["ncit_fallback"]["trigger_terms"] = ["leukemia"]
    return rag_cfg


def test_disease_parenthetical_acronym_stripping_and_token_equiv(monkeypatch) -> None:
    calls: list[tuple[str, str]] = []

    def _fake_retrieve(*, query, source, **kwargs):
        calls.append((query, source))
        if source == "NCI Thesaurus":
            return [
                OntologyCandidate(
                    term_id="NCIT:C3163",
                    label="Chronic Lymphocytic Leukemia",
                    source="NCI Thesaurus",
                    definition=None,
                    synonyms=[],
                    ancestors=[],
                    distance=None,
                    doc_text=None,
                    retrieval_mode=None,
                    query_candidate=query,
                )
            ]
        return []

    monkeypatch.setattr(
        disease_grounder,
        "retrieve_ontology_candidates",
        _fake_retrieve,
    )

    config = _base_rag_config()
    match = disease_grounder.ground_disease(
        "Chronic Lymphoid Leukemia (CLL)",
        "",
        config,
    )

    assert calls
    assert calls[0][0] == "Chronic Lymphoid Leukemia"
    assert any(query == "Chronic Lymphoid Leukemia" for query, _ in calls)

    assert match.status == "MATCHED"
    assert match.matched_term_id == "NCIT:C3163"
    assert match.matched_label == "Chronic Lymphocytic Leukemia"
    assert match.match_type == "token_equiv_similarity"
    assert match.query_used == "Chronic Lymphoid Leukemia"
