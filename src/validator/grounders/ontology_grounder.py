from __future__ import annotations

from typing import Any, Dict, Optional
import logging

from rag.ontology_retrieve import OntologyIndexUnavailable, retrieve_ontology_candidates
from validator.ontology_match import (
    OntologyMatch,
    OntologyMatchResult,
    choose_best_ontology_candidate,
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
    )


def _build_match_from_result(
    field: str,
    raw_value: str,
    ontology: str,
    result: OntologyMatchResult,
) -> OntologyMatch:
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
            alternates=alternates,
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
        alternates=alternates,
    )


def ground_ontology_field(
    raw_value: str,
    context_text: str,
    config: Optional[Dict[str, Any]],
    field: str,
) -> OntologyMatch:
    del context_text
    ontology = _resolve_source(field, config)
    if not isinstance(config, dict) or not config.get("ontology_chroma_enabled", False):
        return _make_index_unavailable_match(field, raw_value, ontology)

    thresholds = thresholds_from_config(config)
    try:
        top_k = int(config.get("ontology_top_k", 20))
    except (TypeError, ValueError):
        top_k = 20
    embedding_model_name = str(
        config.get("ontology_embedding_model_name", "BAAI/bge-base-en-v1.5")
    )
    normalize_embeddings = bool(
        config.get("ontology_embedding_normalize", True)
    )
    persist_path = str(config.get("ontology_chroma_db_path", ""))
    collection_name = str(config.get("ontology_chroma_collection", ""))

    try:
        candidates = retrieve_ontology_candidates(
            query=raw_value,
            source=ontology,
            persist_path=persist_path,
            collection_name=collection_name,
            embedding_model_name=embedding_model_name,
            normalize_embeddings=normalize_embeddings,
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

    result = choose_best_ontology_candidate(raw_value, candidates, thresholds)
    return _build_match_from_result(field, raw_value, ontology, result)
