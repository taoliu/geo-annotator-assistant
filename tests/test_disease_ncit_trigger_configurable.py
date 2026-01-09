from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agent.config import load_config
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
