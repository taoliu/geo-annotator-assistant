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
    assert match.match_type == "synonym_norm_exact"
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


def test_ncit_json_string_synonyms_match_exact_gynecologic_cancer(monkeypatch) -> None:
    def _fake_retrieve(*, query, source, **kwargs):
        if source == "NCI Thesaurus":
            return [
                OntologyCandidate(
                    term_id="NCIT:C4913",
                    label="Malignant Female Reproductive System Neoplasm",
                    source="NCI Thesaurus",
                    definition=None,
                    synonyms='["female reproductive cancer", "gynecologic cancer"]',  # type: ignore[arg-type]
                    ancestors=[],
                    distance=0.25,
                    doc_text=None,
                    retrieval_mode="vector_fallback",
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
    match = disease_grounder.ground_disease("Gynecologic cancer", "", config)

    assert match.status == "MATCHED"
    assert match.selected_source == "NCI Thesaurus"
    assert match.matched_source == "NCI Thesaurus"
    assert match.matched_term_id == "NCIT:C4913"
    assert match.matched_label == "Malignant Female Reproductive System Neoplasm"
    assert match.match_type == "synonym_norm_exact"
    assert match.matched_via == "synonym_norm"
    assert match.matched_synonym == "gynecologic cancer"
    assert match.score == 1.0


def test_strip_leading_model_token_for_disease(monkeypatch) -> None:
    calls: list[tuple[str, str]] = []

    def _fake_retrieve(*, query, source, **kwargs):
        calls.append((query, source))
        return [
            OntologyCandidate(
                term_id="DOID:336",
                label="multiple myeloma",
                source="Human Disease Ontology",
                definition=None,
                synonyms=[],
                ancestors=[],
                distance=0.0,
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
    config["ontology"]["disease"]["ncit_fallback"]["enabled"] = False
    match = disease_grounder.ground_disease("5TGM1 multiple myeloma", "", config)

    assert calls[0][0] == "multiple myeloma"
    assert match.status == "MATCHED"
    assert match.score == 1.0
    assert match.match_type in {"label_exact", "label_norm_exact"}
    assert match.matched_label == "multiple myeloma"
    assert match.query_used == "multiple myeloma"


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


def test_mesothelioma_rewrite_triggers_ncit_and_prefers_exact_ncit(monkeypatch) -> None:
    calls: list[tuple[str, str]] = []

    def _fake_retrieve(*, query, source, **kwargs):
        calls.append((query, source))
        if source == "NCI Thesaurus":
            return [
                OntologyCandidate(
                    term_id="NCIT:C4456",
                    label="Malignant Mesothelioma",
                    source="NCI Thesaurus",
                    definition=None,
                    synonyms=["mesothelioma, unspecified", "mesothelioma"],
                    ancestors=[],
                    distance=0.25,
                    doc_text=None,
                    retrieval_mode="vector_fallback",
                    query_candidate=query,
                )
            ]
        return [
            OntologyCandidate(
                term_id="DOID:1790",
                label="pleural mesothelioma",
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
    match = disease_grounder.ground_disease("Mesothelioma", "", config)

    assert calls[0] == ("mesothelioma, unspecified", "Human Disease Ontology")
    assert ("mesothelioma, unspecified", "NCI Thesaurus") in calls
    assert match.status == "MATCHED"
    assert match.ncit_triggered is True
    assert match.selected_source == "NCI Thesaurus"
    assert match.matched_source == "NCI Thesaurus"
    assert match.matched_term_id == "NCIT:C4456"
    assert match.matched_label == "Malignant Mesothelioma"
    assert match.match_type == "synonym_norm_exact"
    assert match.query_used == "mesothelioma, unspecified"
    assert "NCI Thesaurus" in (match.attempted_sources or [])


def test_mesothelioma_subtype_keeps_exact_doid_without_rewrite(monkeypatch) -> None:
    calls: list[tuple[str, str]] = []

    def _fake_retrieve(*, query, source, **kwargs):
        calls.append((query, source))
        return [
            OntologyCandidate(
                term_id="DOID:1799",
                label="peritoneal mesothelioma",
                source="Human Disease Ontology",
                definition=None,
                synonyms=[],
                ancestors=[],
                distance=0.0,
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
    match = disease_grounder.ground_disease("peritoneal mesothelioma", "", config)

    assert calls[0] == ("peritoneal mesothelioma", "Human Disease Ontology")
    assert "NCI Thesaurus" not in [source for _, source in calls]
    assert match.status == "MATCHED"
    assert match.selected_source == "Human Disease Ontology"
    assert match.matched_label == "peritoneal mesothelioma"
    assert match.query_used == "peritoneal mesothelioma"
