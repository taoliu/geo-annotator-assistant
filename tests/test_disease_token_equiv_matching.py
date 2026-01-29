from __future__ import annotations

import pytest

from agent.ontology_canonicalization import apply_disease_token_equiv_lock
from agent.state import PipelineState
from rag.ontology_retrieve import OntologyCandidate
from validator.ontology_match import OntologyThresholds, choose_best_ontology_candidate


_TOKEN_EQUIVALENCE = {
    "cancer": "oncology_cancer",
    "carcinoma": "oncology_cancer",
    "adenocarcinoma": "oncology_cancer",
    "neoplasm": "oncology_cancer",
    "malignancy": "oncology_cancer",
    "tumor": "tumor",
    "tumour": "tumor",
}


def test_token_equiv_similarity_matches_oncology_synonyms() -> None:
    candidate = OntologyCandidate(
        term_id="NCIT:C105555",
        label="Ovarian High Grade Serous Adenocarcinoma",
        source="NCI Thesaurus",
        definition=None,
        synonyms=[],
        ancestors=[],
        distance=None,
        retrieval_mode=None,
        query_candidate=None,
        doc_text=None,
    )
    thresholds = OntologyThresholds(min_confidence_to_accept=0.8, max_delta_for_ambiguity=0.05)
    result = choose_best_ontology_candidate(
        "High-grade serous ovarian cancer",
        [candidate],
        thresholds,
        token_equivalence=_TOKEN_EQUIVALENCE,
    )

    assert result.status == "MATCHED"
    assert result.match_type == "token_equiv_similarity"
    assert result.confidence == pytest.approx(1.0)
    assert result.original_confidence == pytest.approx(4 / 6)
    assert result.token_equiv_confidence == pytest.approx(1.0)
    assert result.token_equiv_class is not None
    assert "oncology_cancer" in result.token_equiv_class


def test_apply_disease_token_equiv_lock() -> None:
    state = PipelineState(gsm_accession="GSM000")
    state.final_output = {
        "gse_accession": "GSE000",
        "gsm_accession": "GSM000",
        "data_type": "RNA-Seq",
        "organism": "Homo sapiens",
        "tissue_type": "ovary",
        "cell_line": "No",
        "disease": "High-grade serous ovarian cancer",
        "treatment": "None",
    }
    state.ontology_matches = {
        "disease": {
            "status": "MATCHED",
            "match_type": "token_equiv_similarity",
            "matched_label": "Ovarian High Grade Serous Adenocarcinoma",
            "matched_term_id": "NCIT:C105555",
            "matched_source": "NCI Thesaurus",
            "score": 1.0,
        }
    }

    apply_disease_token_equiv_lock(state, None)

    assert state.final_output["disease"] == "Ovarian High Grade Serous Adenocarcinoma"
    assert state.locked_fields["disease"]["reason"] == "disease_token_equiv_similarity"
    assert state.canonicalizations["disease"]["match_type"] == "token_equiv_similarity"
