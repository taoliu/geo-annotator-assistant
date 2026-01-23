"""Ontology grounding for disease with NCIT fallback."""

from __future__ import annotations

from typing import Any, Dict, Optional
import logging
import re

from rag.ontology_retrieve import OntologyIndexUnavailable, retrieve_ontology_candidates
from validator.grounders.ontology_grounder import (
    _build_match_from_result,
    _make_index_unavailable_match,
    _resolve_source,
)
from validator.ontology_match import (
    OntologyMatch,
    OntologyMatchResult,
    choose_best_ontology_candidate,
    is_terminal_exact,
    thresholds_from_config,
)

_LOGGER = logging.getLogger(__name__)
_NCIT_SOURCE = "NCI Thesaurus"
_TRIGGER_TOKEN_RE = re.compile(r"[a-z0-9]+")


def should_query_ncit(raw_label: str, trigger_terms: list[str]) -> bool:
    if not trigger_terms:
        return False
    normalized_label, _ = _normalize_trigger_text(raw_label)
    if not normalized_label:
        return False
    for term in _expand_trigger_terms(trigger_terms):
        if term and term in normalized_label:
            return True
    return False


def _normalize_trigger_text(text: str) -> tuple[str, list[str]]:
    normalized = " ".join(_TRIGGER_TOKEN_RE.findall((text or "").lower()))
    tokens = normalized.split() if normalized else []
    return normalized, tokens


def _singularize_token(token: str) -> str:
    if token.endswith("ies") and len(token) > 3:
        return f"{token[:-3]}y"
    if token.endswith("es") and len(token) > 2:
        return token[:-2]
    if token.endswith("s") and len(token) > 3:
        return token[:-1]
    return token


def _pluralize_token(token: str) -> str:
    if not token:
        return token
    if token.endswith("y") and len(token) > 2 and token[-2] not in "aeiou":
        return f"{token[:-1]}ies"
    if token.endswith(("s", "x", "z", "ch", "sh")):
        return f"{token}es"
    return f"{token}s"


def _expand_trigger_terms(trigger_terms: list[str]) -> set[str]:
    expanded: set[str] = set()
    for term in trigger_terms:
        normalized, tokens = _normalize_trigger_text(term)
        if not normalized:
            continue
        expanded.add(normalized)
        if not tokens:
            continue
        last = tokens[-1]
        singular = _singularize_token(last)
        plural = _pluralize_token(last)
        for variant in {singular, plural}:
            if variant and variant != last:
                expanded.add(" ".join(tokens[:-1] + [variant]))
    return expanded


def _extract_ncit_config(config: Optional[Dict[str, Any]]) -> tuple[bool, list[str]]:
    if not isinstance(config, dict):
        return False, []
    ontology_cfg = config.get("ontology") if isinstance(config.get("ontology"), dict) else {}
    disease_cfg = ontology_cfg.get("disease") if isinstance(ontology_cfg.get("disease"), dict) else {}
    ncit_cfg = disease_cfg.get("ncit_fallback") if isinstance(disease_cfg.get("ncit_fallback"), dict) else {}
    enabled = bool(ncit_cfg.get("enabled", True))
    trigger_terms = ncit_cfg.get("trigger_terms")
    if not isinstance(trigger_terms, list):
        return enabled, []
    normalized = [str(term).lower() for term in trigger_terms if str(term).strip()]
    return enabled, normalized


def _resolve_embedding_config(
    config: Dict[str, Any],
) -> tuple[int, str, str, bool, str, str]:
    ontology_cfg = config.get("ontology") if isinstance(config.get("ontology"), dict) else {}
    try:
        top_k = int(config.get("k", 20))
    except (TypeError, ValueError):
        top_k = 20
    embedding_cfg = ontology_cfg.get("embedding") if isinstance(ontology_cfg.get("embedding"), dict) else {}
    embedding_model_name = str(embedding_cfg.get("model_name", "BAAI/bge-base-en-v1.5"))
    embedding_device = str(embedding_cfg.get("device", "cpu"))
    normalize_embeddings = bool(embedding_cfg.get("normalize_embeddings", True))
    persist_path = str(config.get("persist_path", ""))
    collection_name = str(config.get("collection_name", ""))
    return (
        top_k,
        embedding_model_name,
        embedding_device,
        normalize_embeddings,
        persist_path,
        collection_name,
    )


def _ground_source(
    raw_value: str,
    source: str,
    config: Dict[str, Any],
    thresholds,
) -> tuple[OntologyMatchResult, bool, bool]:
    (
        top_k,
        embedding_model_name,
        embedding_device,
        normalize_embeddings,
        persist_path,
        collection_name,
    ) = _resolve_embedding_config(config)
    candidates = retrieve_ontology_candidates(
        query=raw_value,
        source=source,
        persist_path=persist_path,
        collection_name=collection_name,
        embedding_model_name=embedding_model_name,
        normalize_embeddings=normalize_embeddings,
        embedding_device=embedding_device,
        top_k=top_k,
    )
    result = choose_best_ontology_candidate(raw_value, candidates, thresholds)
    vector_fallback_used = any(
        candidate.retrieval_mode == "vector_fallback" for candidate in candidates
    )
    terminal_exact = is_terminal_exact(
        result.status,
        float(result.confidence or 0.0),
        str(result.match_type or ""),
    )
    return result, terminal_exact, vector_fallback_used


def ground_disease(
    raw_value: str,
    context_text: str,
    config: Optional[Dict[str, Any]],
) -> OntologyMatch:
    del context_text
    doid_source = _resolve_source("disease", config)
    if not isinstance(config, dict):
        return _make_index_unavailable_match(
            "disease",
            raw_value,
            doid_source,
        )
    ontology_cfg = config.get("ontology") if isinstance(config.get("ontology"), dict) else {}
    if not ontology_cfg.get("enabled", False):
        return _make_index_unavailable_match(
            "disease",
            raw_value,
            doid_source,
        )

    ncit_enabled, trigger_terms = _extract_ncit_config(config)
    trigger_possible = bool(trigger_terms)
    attempted_sources = [doid_source]
    thresholds = thresholds_from_config(config)

    try:
        doid_result, doid_terminal_exact, doid_vector_fallback = _ground_source(
            raw_value,
            doid_source,
            config,
            thresholds,
        )
    except OntologyIndexUnavailable as exc:
        _LOGGER.warning(
            "Ontology index unavailable for field=%s source=%s: %s",
            "disease",
            doid_source,
            exc,
        )
        return _make_index_unavailable_match(
            "disease",
            raw_value,
            doid_source,
            ncit_fallback_enabled=ncit_enabled,
            ncit_triggered=False,
            ncit_trigger_terms_used=trigger_terms if trigger_possible else [],
            attempted_sources=attempted_sources,
            selected_source=doid_source,
            selection_rule="doid_index_unavailable",
        )

    if doid_terminal_exact:
        return _build_match_from_result(
            "disease",
            raw_value,
            doid_source,
            doid_result,
            terminal_exact=doid_terminal_exact,
            vector_fallback_skipped=doid_terminal_exact and not doid_vector_fallback,
            ncit_fallback_enabled=ncit_enabled,
            ncit_triggered=False,
            ncit_trigger_terms_used=trigger_terms if trigger_possible else [],
            attempted_sources=attempted_sources,
            selected_source=doid_source,
            selection_rule="doid_terminal_exact",
        )

    if not ncit_enabled:
        return _build_match_from_result(
            "disease",
            raw_value,
            doid_source,
            doid_result,
            terminal_exact=doid_terminal_exact,
            vector_fallback_skipped=doid_terminal_exact and not doid_vector_fallback,
            ncit_fallback_enabled=ncit_enabled,
            ncit_triggered=False,
            ncit_trigger_terms_used=trigger_terms if trigger_possible else [],
            attempted_sources=attempted_sources,
            selected_source=doid_source,
            selection_rule="ncit_disabled",
        )

    if not trigger_possible:
        return _build_match_from_result(
            "disease",
            raw_value,
            doid_source,
            doid_result,
            terminal_exact=doid_terminal_exact,
            vector_fallback_skipped=doid_terminal_exact and not doid_vector_fallback,
            ncit_fallback_enabled=ncit_enabled,
            ncit_triggered=False,
            ncit_trigger_terms_used=[],
            attempted_sources=attempted_sources,
            selected_source=doid_source,
            selection_rule="ncit_trigger_terms_empty",
        )

    if not should_query_ncit(raw_value, trigger_terms):
        return _build_match_from_result(
            "disease",
            raw_value,
            doid_source,
            doid_result,
            terminal_exact=doid_terminal_exact,
            vector_fallback_skipped=doid_terminal_exact and not doid_vector_fallback,
            ncit_fallback_enabled=ncit_enabled,
            ncit_triggered=False,
            ncit_trigger_terms_used=trigger_terms,
            attempted_sources=attempted_sources,
            selected_source=doid_source,
            selection_rule="ncit_trigger_false",
        )

    attempted_sources.append(_NCIT_SOURCE)
    try:
        ncit_result, ncit_terminal_exact, ncit_vector_fallback = _ground_source(
            raw_value,
            _NCIT_SOURCE,
            config,
            thresholds,
        )
    except OntologyIndexUnavailable as exc:
        _LOGGER.warning(
            "Ontology index unavailable for field=%s source=%s: %s",
            "disease",
            _NCIT_SOURCE,
            exc,
        )
        return _build_match_from_result(
            "disease",
            raw_value,
            doid_source,
            doid_result,
            terminal_exact=doid_terminal_exact,
            vector_fallback_skipped=doid_terminal_exact and not doid_vector_fallback,
            ncit_fallback_enabled=ncit_enabled,
            ncit_triggered=True,
            ncit_trigger_terms_used=trigger_terms,
            attempted_sources=attempted_sources,
            selected_source=doid_source,
            selection_rule="ncit_index_unavailable",
        )

    if ncit_terminal_exact:
        return _build_match_from_result(
            "disease",
            raw_value,
            _NCIT_SOURCE,
            ncit_result,
            terminal_exact=ncit_terminal_exact,
            vector_fallback_skipped=ncit_terminal_exact and not ncit_vector_fallback,
            ncit_fallback_enabled=ncit_enabled,
            ncit_triggered=True,
            ncit_trigger_terms_used=trigger_terms,
            attempted_sources=attempted_sources,
            selected_source=_NCIT_SOURCE,
            selection_rule="ncit_terminal_exact",
        )

    doid_score = float(doid_result.confidence or 0.0)
    ncit_score = float(ncit_result.confidence or 0.0)
    if ncit_score > doid_score:
        return _build_match_from_result(
            "disease",
            raw_value,
            _NCIT_SOURCE,
            ncit_result,
            terminal_exact=ncit_terminal_exact,
            vector_fallback_skipped=ncit_terminal_exact and not ncit_vector_fallback,
            ncit_fallback_enabled=ncit_enabled,
            ncit_triggered=True,
            ncit_trigger_terms_used=trigger_terms,
            attempted_sources=attempted_sources,
            selected_source=_NCIT_SOURCE,
            selection_rule="score_preference_ncit",
        )

    return _build_match_from_result(
        "disease",
        raw_value,
        doid_source,
        doid_result,
        terminal_exact=doid_terminal_exact,
        vector_fallback_skipped=doid_terminal_exact and not doid_vector_fallback,
        ncit_fallback_enabled=ncit_enabled,
        ncit_triggered=True,
        ncit_trigger_terms_used=trigger_terms,
        attempted_sources=attempted_sources,
        selected_source=doid_source,
        selection_rule="score_tie_prefer_doid",
    )
