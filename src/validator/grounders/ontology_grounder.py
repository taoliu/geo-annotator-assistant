from __future__ import annotations

from typing import Any, Dict, Optional
import logging

from rag.ontology_retrieve import OntologyIndexUnavailable, retrieve_ontology_candidates
from validator.ontology_match import (
    OntologyMatch,
    OntologyMatchResult,
    choose_best_ontology_candidate,
    is_terminal_exact,
    thresholds_from_config,
)

_DEFAULT_SOURCES_BY_FIELD = {
    "tissue_type": "Uberon Ontology",
    "disease": "Human Disease Ontology",
    "cell_line": "Cellosaurus",
    "data_type": "Experimental Factor Ontology",
}

_LOGGER = logging.getLogger(__name__)


def _resolve_source(field: str, config: Optional[Dict[str, Any]]) -> str:
    if isinstance(config, dict):
        ontology_cfg = config.get("ontology") if isinstance(config.get("ontology"), dict) else None
        sources = None
        if isinstance(ontology_cfg, dict):
            sources = ontology_cfg.get("sources_by_field")
        if sources is None:
            sources = config.get("ontology_sources_by_field")
        if isinstance(sources, dict):
            source_value = sources.get(field)
            if source_value:
                return str(source_value)
    return _DEFAULT_SOURCES_BY_FIELD.get(field, field)


def _make_index_unavailable_match(
    field: str,
    raw_value: str,
    ontology: str,
    *,
    query_used: Optional[str] = None,
    ncit_fallback_enabled: Optional[bool] = None,
    ncit_triggered: Optional[bool] = None,
    ncit_trigger_terms_used: Optional[list[str]] = None,
    attempted_sources: Optional[list[str]] = None,
    selected_source: Optional[str] = None,
    selection_rule: Optional[str] = None,
) -> OntologyMatch:
    return OntologyMatch(
        field=field,
        raw_value=raw_value,
        ontology=ontology,
        status="INDEX_UNAVAILABLE",
        matched_term_id=None,
        matched_label=None,
        matched_source=None,
        match_type=None,
        score=None,
        alternates=[],
        query_used=query_used,
        ncit_fallback_enabled=ncit_fallback_enabled,
        ncit_triggered=ncit_triggered,
        ncit_trigger_terms_used=ncit_trigger_terms_used,
        attempted_sources=attempted_sources,
        selected_source=selected_source,
        selection_rule=selection_rule,
    )


def _build_match_from_result(
    field: str,
    raw_value: str,
    ontology: str,
    result: OntologyMatchResult,
    *,
    terminal_exact: bool = False,
    vector_fallback_skipped: Optional[bool] = None,
    query_used: Optional[str] = None,
    ncit_fallback_enabled: Optional[bool] = None,
    ncit_triggered: Optional[bool] = None,
    ncit_trigger_terms_used: Optional[list[str]] = None,
    attempted_sources: Optional[list[str]] = None,
    selected_source: Optional[str] = None,
    selection_rule: Optional[str] = None,
) -> OntologyMatch:
    if terminal_exact and result.best is not None:
        alternates = [result.best.to_dict()]
    else:
        alternates = [alt.to_dict() for alt in result.alternates]
    if result.status == "MATCHED" and result.best is not None:
        return OntologyMatch(
            field=field,
            raw_value=raw_value,
            ontology=ontology,
            status=result.status,
            matched_term_id=result.best.term_id,
            matched_label=result.best.label,
            matched_source=result.best.source,
            match_type=result.match_type,
            score=result.confidence,
            original_score=result.original_confidence,
            token_equiv_score=result.token_equiv_confidence,
            token_equiv_class=result.token_equiv_class,
            tie_break_rule=result.tie_break_rule,
            alternates=alternates,
            matched_via=result.matched_via,
            matched_synonym=result.matched_synonym,
            vector_fallback_skipped=vector_fallback_skipped,
            query_used=query_used,
            ncit_fallback_enabled=ncit_fallback_enabled,
            ncit_triggered=ncit_triggered,
            ncit_trigger_terms_used=ncit_trigger_terms_used,
            attempted_sources=attempted_sources,
            selected_source=selected_source,
            selection_rule=selection_rule,
        )
    return OntologyMatch(
        field=field,
        raw_value=raw_value,
        ontology=ontology,
        status=result.status,
        matched_term_id=None,
        matched_label=None,
        matched_source=None,
        match_type=result.match_type,
        score=result.confidence,
        original_score=result.original_confidence,
        token_equiv_score=result.token_equiv_confidence,
        token_equiv_class=result.token_equiv_class,
        tie_break_rule=result.tie_break_rule,
        alternates=alternates,
        matched_via=None,
        matched_synonym=None,
        vector_fallback_skipped=vector_fallback_skipped,
        query_used=query_used,
        ncit_fallback_enabled=ncit_fallback_enabled,
        ncit_triggered=ncit_triggered,
        ncit_trigger_terms_used=ncit_trigger_terms_used,
        attempted_sources=attempted_sources,
        selected_source=selected_source,
        selection_rule=selection_rule,
    )


def ground_ontology_field(
    raw_value: str,
    context_text: str,
    config: Optional[Dict[str, Any]],
    field: str,
) -> OntologyMatch:
    del context_text
    ontology = _resolve_source(field, config)
    if not isinstance(config, dict):
        return _make_index_unavailable_match(field, raw_value, ontology)
    ontology_cfg = config.get("ontology") if isinstance(config.get("ontology"), dict) else {}
    if not ontology_cfg.get("enabled", False):
        return _make_index_unavailable_match(field, raw_value, ontology)

    thresholds = thresholds_from_config(config)
    try:
        top_k = int(config.get("k", 20))
    except (TypeError, ValueError):
        top_k = 20
    embedding_cfg = ontology_cfg.get("embedding") if isinstance(ontology_cfg.get("embedding"), dict) else {}
    embedding_model_name = str(
        embedding_cfg.get("model_name", "BAAI/bge-base-en-v1.5")
    )
    embedding_device = str(
        embedding_cfg.get("device", "cpu")
    )
    normalize_embeddings = bool(
        embedding_cfg.get("normalize_embeddings", True)
    )
    persist_path = str(config.get("persist_path", ""))
    collection_name = str(config.get("collection_name", ""))

    try:
        candidates = retrieve_ontology_candidates(
            query=raw_value,
            source=ontology,
            persist_path=persist_path,
            collection_name=collection_name,
            embedding_model_name=embedding_model_name,
            normalize_embeddings=normalize_embeddings,
            embedding_device=embedding_device,
            top_k=top_k,
        )
    except OntologyIndexUnavailable as exc:
        _LOGGER.warning(
            "Ontology index unavailable for field=%s source=%s collection=%s path=%s: %s",
            field,
            ontology,
            collection_name,
            persist_path,
            exc,
        )
        return _make_index_unavailable_match(field, raw_value, ontology)

    result = choose_best_ontology_candidate(
        raw_value,
        candidates,
        thresholds,
        tie_breaker="cell_line" if field == "cell_line" else None,
    )
    vector_fallback_used = any(
        candidate.retrieval_mode == "vector_fallback" for candidate in candidates
    )
    terminal_exact = is_terminal_exact(
        result.status,
        float(result.confidence or 0.0),
        str(result.match_type or ""),
    )
    return _build_match_from_result(
        field,
        raw_value,
        ontology,
        result,
        terminal_exact=terminal_exact,
        vector_fallback_skipped=terminal_exact and not vector_fallback_used,
    )
