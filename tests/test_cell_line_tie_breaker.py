from __future__ import annotations

from rag.ontology_retrieve import OntologyCandidate
from validator.ontology_match import OntologyThresholds, choose_best_ontology_candidate


def test_cell_line_exact_tie_break_prefers_raw_label_match() -> None:
    candidate_exact = OntologyCandidate(
        term_id="CVCL:0035",
        label="PC-3",
        source="Cellosaurus",
        definition=None,
        synonyms=[],
        ancestors=[],
        distance=None,
        doc_text=None,
        retrieval_mode="meta_exact",
        query_candidate=None,
    )
    candidate_compact = OntologyCandidate(
        term_id="CVCL:E2RM",
        label="PC3",
        source="Cellosaurus",
        definition=None,
        synonyms=[],
        ancestors=[],
        distance=None,
        doc_text=None,
        retrieval_mode="meta_exact",
        query_candidate=None,
    )
    thresholds = OntologyThresholds(min_confidence_to_accept=0.80, max_delta_for_ambiguity=0.05)

    result = choose_best_ontology_candidate(
        "PC-3",
        [candidate_exact, candidate_compact],
        thresholds,
        tie_breaker="cell_line",
    )

    assert result.status == "MATCHED"
    assert result.match_type in {
        "label_exact",
        "label_norm_exact",
        "synonym_exact",
        "synonym_norm_exact",
    }
    assert result.best is not None
    assert result.best.term_id == "CVCL:0035"
    assert result.tie_break_rule == "raw_label_exact_match"
