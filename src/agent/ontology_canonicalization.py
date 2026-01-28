"""Canonicalization and locking for terminal exact ontology matches."""

from __future__ import annotations

from typing import Any, Dict, Optional
import re

from agent.state import PipelineState
from validator.ontology_match import is_terminal_exact

_DISEASE_GENERALIZATION_FLAG = "disease_generalized_for_ontology"
_DISEASE_PARENT_SOURCES = {"human disease ontology", "nci thesaurus"}
_DISEASE_SUBSTRING_RE = re.compile(r"[-\s]+")
_TISSUE_PLACEHOLDER_FLAG = "tissue_type_non_anatomical_placeholder"
_TISSUE_PLACEHOLDER_MATCHED_VIA = "non_anatomical_placeholder"
_DISEASE_MODEL_FLAG = "disease_model_identifier_not_ontology"
_DISEASE_MODEL_MATCHED_VIA = "model_identifier"


def _extract_match_values(match: Any) -> tuple[Optional[str], float, Optional[str], Optional[str], Optional[str], Optional[str]]:
    if isinstance(match, dict):
        status = match.get("status")
        score = match.get("score")
        match_type = match.get("match_type")
        label = match.get("matched_label")
        term_id = match.get("matched_term_id")
        source = match.get("matched_source")
    else:
        status = getattr(match, "status", None)
        score = getattr(match, "score", None)
        match_type = getattr(match, "match_type", None)
        label = getattr(match, "matched_label", None)
        term_id = getattr(match, "matched_term_id", None)
        source = getattr(match, "matched_source", None)
    try:
        score_value = float(score) if score is not None else 0.0
    except (TypeError, ValueError):
        score_value = 0.0
    return status, score_value, match_type, label, term_id, source


def _ontology_cfg(config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not isinstance(config, dict):
        return {}
    rag_cfg = config.get("rag") if isinstance(config.get("rag"), dict) else {}
    ontology_cfg = rag_cfg.get("ontology") if isinstance(rag_cfg.get("ontology"), dict) else {}
    return dict(ontology_cfg) if ontology_cfg else {}


def apply_terminal_exact_canonicalization_and_lock(
    state: PipelineState,
    config: Optional[Dict[str, Any]],
) -> None:
    if state.final_output is None:
        return
    if not state.ontology_matches:
        return

    ontology_cfg = _ontology_cfg(config)
    canonicalize_enabled = bool(
        ontology_cfg.get("canonicalize_terminal_exact_labels", False)
    )
    lock_enabled = bool(ontology_cfg.get("lock_terminal_exact_fields", False))
    if not canonicalize_enabled and not lock_enabled:
        return

    # Locking implies canonicalization to avoid freezing non-canonical strings.
    canonicalize_for_lock = canonicalize_enabled or lock_enabled
    canonicalizations = dict(state.canonicalizations)
    locked_fields = dict(state.locked_fields)

    for field in sorted(state.ontology_matches):
        match = state.ontology_matches[field]
        status, score, match_type, label, term_id, source = _extract_match_values(match)
        if not is_terminal_exact(str(status or ""), score, str(match_type or "")):
            continue

        original_value = state.final_output.get(field)
        if canonicalize_for_lock and label:
            state.final_output[field] = label
            canonicalizations[field] = {
                "field": field,
                "original_value": original_value,
                "canonical_value": label,
                "term_id": term_id,
                "source": source,
                "match_type": match_type,
            }

        if lock_enabled:
            locked_fields[field] = {
                "term_id": term_id,
                "label": label,
                "source": source,
                "reason": "ontology_terminal_exact",
            }

    if lock_enabled and locked_fields:
        for field in list(state.semantic_errors):
            if field in locked_fields:
                state.semantic_errors.pop(field, None)
        for field in list(state.ontology_failures):
            if field in locked_fields:
                state.ontology_failures.pop(field, None)

    state.canonicalizations = canonicalizations
    state.locked_fields = locked_fields


def _normalize_substring_text(text: str) -> str:
    if not text:
        return ""
    normalized = _DISEASE_SUBSTRING_RE.sub(" ", text.lower())
    return " ".join(normalized.split())


def _extract_match_attr(match: Any, attr: str) -> Any:
    if isinstance(match, dict):
        return match.get(attr)
    return getattr(match, attr, None)


def apply_disease_modifier_generalization(
    state: PipelineState,
    config: Optional[Dict[str, Any]],
) -> None:
    del config
    if state.final_output is None:
        return
    match = state.ontology_matches.get("disease")
    if not match:
        return
    if state.locked_fields.get("disease", {}).get("reason") == _DISEASE_GENERALIZATION_FLAG:
        return
    status = _extract_match_attr(match, "status")
    if status != "LOW_CONFIDENCE":
        return
    alternates = _extract_match_attr(match, "alternates")
    if not isinstance(alternates, list) or not alternates:
        return

    top = alternates[0] if alternates else None
    if not isinstance(top, dict):
        return
    label = top.get("label")
    term_id = top.get("term_id")
    source = top.get("source")
    if not isinstance(label, str) or not label.strip():
        return
    if not isinstance(source, str) or source.strip().lower() not in _DISEASE_PARENT_SOURCES:
        return

    raw_value = _extract_match_attr(match, "raw_value") or state.final_output.get("disease") or ""
    if not isinstance(raw_value, str):
        raw_value = str(raw_value)
    raw_norm = _normalize_substring_text(raw_value)
    label_norm = _normalize_substring_text(label)
    if not raw_norm or not label_norm or label_norm not in raw_norm:
        return

    original_value = state.final_output.get("disease")
    state.final_output["disease"] = label

    canonicalizations = dict(state.canonicalizations)
    canonicalizations["disease"] = {
        "field": "disease",
        "original_value": original_value,
        "canonical_value": label,
        "term_id": term_id,
        "source": source,
        "match_type": "parent_substring",
    }
    state.canonicalizations = canonicalizations

    locked_fields = dict(state.locked_fields)
    locked_fields["disease"] = {
        "term_id": term_id,
        "label": label,
        "source": source,
        "reason": _DISEASE_GENERALIZATION_FLAG,
    }
    state.locked_fields = locked_fields

    state.semantic_errors.pop("disease", None)
    state.ontology_failures.pop("disease", None)
    if _DISEASE_GENERALIZATION_FLAG not in state.flags:
        state.flags.append(_DISEASE_GENERALIZATION_FLAG)


def apply_tissue_placeholder_fallback(
    state: PipelineState,
    config: Optional[Dict[str, Any]],
) -> None:
    del config
    if state.final_output is None:
        return
    match = state.ontology_matches.get("tissue_type")
    if not match:
        return
    if state.locked_fields.get("tissue_type", {}).get("reason") == _TISSUE_PLACEHOLDER_FLAG:
        return
    matched_via = _extract_match_attr(match, "matched_via")
    if matched_via != _TISSUE_PLACEHOLDER_MATCHED_VIA:
        return

    original_value = state.final_output.get("tissue_type")
    state.final_output["tissue_type"] = "Unknown"

    locked_fields = dict(state.locked_fields)
    locked_fields["tissue_type"] = {
        "term_id": None,
        "label": "Unknown",
        "source": None,
        "reason": _TISSUE_PLACEHOLDER_FLAG,
        "original_value": original_value,
    }
    state.locked_fields = locked_fields

    state.semantic_errors.pop("tissue_type", None)
    state.ontology_failures.pop("tissue_type", None)
    if _TISSUE_PLACEHOLDER_FLAG not in state.flags:
        state.flags.append(_TISSUE_PLACEHOLDER_FLAG)


def apply_disease_model_fallback(
    state: PipelineState,
    config: Optional[Dict[str, Any]],
) -> None:
    del config
    if state.final_output is None:
        return
    match = state.ontology_matches.get("disease")
    if not match:
        return
    if state.locked_fields.get("disease", {}).get("reason") == _DISEASE_MODEL_FLAG:
        return
    matched_via = _extract_match_attr(match, "matched_via")
    if matched_via != _DISEASE_MODEL_MATCHED_VIA:
        return

    original_value = state.final_output.get("disease")
    state.final_output["disease"] = "Unknown"

    locked_fields = dict(state.locked_fields)
    locked_fields["disease"] = {
        "term_id": None,
        "label": "Unknown",
        "source": None,
        "reason": _DISEASE_MODEL_FLAG,
        "original_value": original_value,
    }
    state.locked_fields = locked_fields

    state.semantic_errors.pop("disease", None)
    state.ontology_failures.pop("disease", None)
    if _DISEASE_MODEL_FLAG not in state.flags:
        state.flags.append(_DISEASE_MODEL_FLAG)
