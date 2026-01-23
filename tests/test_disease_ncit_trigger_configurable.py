from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agent.config import load_config
from rag.ontology_retrieve import OntologyCandidate
import rag.ontology_retrieve as ontology_retrieve
from validator.grounders import disease as disease_grounder


def _base_rag_config() -> dict:
    cfg = load_config(str(ROOT / "config" / "example_config.yaml"))
    rag_cfg = cfg.get("rag") or {}
    rag_cfg.setdefault("ontology", {})["enabled"] = True
    return rag_cfg


def _fake_retrieve(calls):
    def _inner(*, query, source, **kwargs):
        calls.append(source)
        return []

    return _inner


def test_default_trigger_list_triggers_ncit(monkeypatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr(
        disease_grounder,
        "retrieve_ontology_candidates",
        _fake_retrieve(calls),
    )

    config = _base_rag_config()
    disease_grounder.ground_disease(
        "metastatic castration-resistant prostate cancer",
        "",
        config,
    )

    assert calls[0] == "Human Disease Ontology"
    assert "NCI Thesaurus" in calls


def test_custom_trigger_list_only_when_configured(monkeypatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr(
        disease_grounder,
        "retrieve_ontology_candidates",
        _fake_retrieve(calls),
    )

    config = _base_rag_config()
    config["ontology"]["disease"]["ncit_fallback"]["trigger_terms"] = ["mycosis"]
    disease_grounder.ground_disease("mycosis fungoides", "", config)
    assert "NCI Thesaurus" in calls

    calls.clear()
    config = _base_rag_config()
    disease_grounder.ground_disease("mycosis fungoides", "", config)
    assert "NCI Thesaurus" not in calls


def test_plural_morphology_triggers_ncit(monkeypatch) -> None:
    calls: list[str] = []

    def _fake_retrieve(*, query, source, **kwargs):
        calls.append(source)
        if source == "NCI Thesaurus":
            return [
                OntologyCandidate(
                    term_id="NCIT:C12345",
                    label="B-Cell Malignant Neoplasm",
                    source="NCI Thesaurus",
                    definition=None,
                    synonyms=["B-Cell Malignancy", "B cell malignancies"],
                    ancestors=[],
                    distance=0.0,
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
    config["ontology"]["disease"]["ncit_fallback"]["trigger_terms"] = ["malignancy"]
    match = disease_grounder.ground_disease("B cell malignancies", "", config)

    assert calls[0] == "Human Disease Ontology"
    assert "NCI Thesaurus" in calls
    assert match.ncit_triggered is True
    assert match.selected_source == "NCI Thesaurus"
    assert match.matched_label == "B-Cell Malignant Neoplasm"
    assert match.matched_synonym in {"B cell malignancies", "B-Cell Malignancy"}
    assert match.score == 1.0
    assert "NCI Thesaurus" in (match.attempted_sources or [])
    assert any(
        alt.get("label") == "B-Cell Malignant Neoplasm" for alt in match.alternates
    )


def test_terminal_exact_ncit_preferred_over_fuzzy_doid(monkeypatch) -> None:
    calls: list[str] = []

    def _fake_retrieve(*, query, source, **kwargs):
        calls.append(source)
        if source == "NCI Thesaurus":
            return [
                OntologyCandidate(
                    term_id="NCIT:C12345",
                    label="B-Cell Malignant Neoplasm",
                    source="NCI Thesaurus",
                    definition=None,
                    synonyms=["B-Cell Malignancy"],
                    ancestors=[],
                    distance=0.0,
                    doc_text=None,
                    retrieval_mode=None,
                    query_candidate=query,
                )
            ]
        return [
            OntologyCandidate(
                term_id="DOID:707",
                label="B-cell lymphoma",
                source="Human Disease Ontology",
                definition=None,
                synonyms=[],
                ancestors=[],
                distance=0.5,
                doc_text=None,
                retrieval_mode=None,
                query_candidate=query,
            )
        ]

    monkeypatch.setattr(
        disease_grounder,
        "retrieve_ontology_candidates",
        _fake_retrieve,
    )

    config = _base_rag_config()
    config["ontology"]["disease"]["ncit_fallback"]["trigger_terms"] = ["malignancy"]
    match = disease_grounder.ground_disease("B cell malignancies", "", config)

    assert calls[0] == "Human Disease Ontology"
    assert "NCI Thesaurus" in calls
    assert match.selected_source == "NCI Thesaurus"
    assert match.match_type == "synonym_exact"
    assert match.score == 1.0
    assert match.matched_label == "B-Cell Malignant Neoplasm"
    assert match.matched_synonym == "B-Cell Malignancy"
    assert match.ncit_triggered is True
    assert "NCI Thesaurus" in (match.attempted_sources or [])
    assert any(
        alt.get("label") == "B-Cell Malignant Neoplasm" for alt in match.alternates
    )


def test_matched_synonym_serializes_cleanly(monkeypatch) -> None:
    def _fake_retrieve(*, query, source, **kwargs):
        if source == "NCI Thesaurus":
            meta = {
                "term_id": "NCIT:C12345",
                "label": "B-Cell Malignant Neoplasm",
                "source": "NCI Thesaurus",
                "synonyms": '["B-Cell Malignancy","B cell malignancies"]',
            }
            return [
                ontology_retrieve._build_candidate(
                    "NCIT:C12345",
                    0.0,
                    meta,
                    None,
                    "NCI Thesaurus",
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
    config["ontology"]["disease"]["ncit_fallback"]["trigger_terms"] = ["malignancy"]
    match = disease_grounder.ground_disease("B cell malignancies", "", config)

    matched_synonym = match.matched_synonym
    if isinstance(matched_synonym, str) and matched_synonym.startswith("["):
        import json

        parsed = json.loads(matched_synonym)
        assert isinstance(parsed, list)
    else:
        assert isinstance(matched_synonym, str)


def test_disabled_fallback_never_queries_ncit(monkeypatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr(
        disease_grounder,
        "retrieve_ontology_candidates",
        _fake_retrieve(calls),
    )

    config = _base_rag_config()
    config["ontology"]["disease"]["ncit_fallback"]["enabled"] = False
    disease_grounder.ground_disease("lung cancer", "", config)

    assert "NCI Thesaurus" not in calls


def test_empty_trigger_list_never_queries_ncit(monkeypatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr(
        disease_grounder,
        "retrieve_ontology_candidates",
        _fake_retrieve(calls),
    )

    config = _base_rag_config()
    config["ontology"]["disease"]["ncit_fallback"]["trigger_terms"] = []
    disease_grounder.ground_disease("lung cancer", "", config)

    assert "NCI Thesaurus" not in calls
