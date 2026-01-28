from __future__ import annotations

from typing import Dict, Optional
import re

from validator.failure_codes import (
    ONTOLOGY_AMBIGUOUS_CELL_LINE,
    ONTOLOGY_AMBIGUOUS_DATA_TYPE,
    ONTOLOGY_AMBIGUOUS_DISEASE,
    ONTOLOGY_AMBIGUOUS_TISSUE_TYPE,
    ONTOLOGY_INDEX_UNAVAILABLE,
    ONTOLOGY_LOW_CONFIDENCE_CELL_LINE,
    ONTOLOGY_LOW_CONFIDENCE_DATA_TYPE,
    ONTOLOGY_LOW_CONFIDENCE_DISEASE,
    ONTOLOGY_LOW_CONFIDENCE_TISSUE_TYPE,
    ONTOLOGY_NO_MATCH_CELL_LINE,
    ONTOLOGY_NO_MATCH_DATA_TYPE,
    ONTOLOGY_NO_MATCH_DISEASE,
    ONTOLOGY_NO_MATCH_TISSUE_TYPE,
)
from validator.ontology_match import OntologyMatch
from validator.cell_line_rules import is_cell_line_cell_type

try:
    from validator.grounders import data_type as _data_type_grounder
except Exception:
    _data_type_grounder = None

try:
    from validator.grounders import tissue_type as _tissue_type_grounder
except Exception:
    _tissue_type_grounder = None

try:
    from validator.grounders import cell_line as _cell_line_grounder
except Exception:
    _cell_line_grounder = None

try:
    from validator.grounders import disease as _disease_grounder
except Exception:
    _disease_grounder = None

_DEFAULT_SOURCES_BY_FIELD = {
    "data_type": "Experimental Factor Ontology",
    "tissue_type": "Uberon Ontology",
    "cell_line": "Cellosaurus",
    "disease": "Human Disease Ontology",
}

_FALLBACK_VALUES = {
    "tissue_type": {"Unknown"},
    "cell_line": {"No"},
    "disease": {"Healthy", "Unknown"},
}

_NON_ANATOMICAL_TISSUE_PLACEHOLDERS = {
    "tumor",
    "tumour",
    "tumor tissue",
    "tumour tissue",
    "tumor sample",
    "tumour sample",
    "tumor samples",
    "tumour samples",
}
_PLACEHOLDER_NORMALIZE_RE = re.compile(r"[^a-z0-9]+")
_DISEASE_MODEL_IDENTIFIERS = {
    "ct26",
    "mc38",
    "b16",
    "4t1",
    "llc",
}
_DISEASE_MODEL_PHRASES = {
    "mouse tumor model",
    "syngeneic tumor model",
    "xenograft model",
}
_DISEASE_EXPLICIT_TERMS = {
    "cancer",
    "carcinoma",
    "adenocarcinoma",
    "leukemia",
    "lymphoma",
    "melanoma",
    "sarcoma",
    "glioma",
    "glioblastoma",
    "myeloma",
    "blastoma",
}

_FIELD_FAILURE_CODES = {
    "tissue_type": {
        "NO_MATCH": ONTOLOGY_NO_MATCH_TISSUE_TYPE,
        "AMBIGUOUS": ONTOLOGY_AMBIGUOUS_TISSUE_TYPE,
        "LOW_CONFIDENCE": ONTOLOGY_LOW_CONFIDENCE_TISSUE_TYPE,
    },
    "disease": {
        "NO_MATCH": ONTOLOGY_NO_MATCH_DISEASE,
        "AMBIGUOUS": ONTOLOGY_AMBIGUOUS_DISEASE,
        "LOW_CONFIDENCE": ONTOLOGY_LOW_CONFIDENCE_DISEASE,
    },
    "cell_line": {
        "NO_MATCH": ONTOLOGY_NO_MATCH_CELL_LINE,
        "AMBIGUOUS": ONTOLOGY_AMBIGUOUS_CELL_LINE,
        "LOW_CONFIDENCE": ONTOLOGY_LOW_CONFIDENCE_CELL_LINE,
    },
    "data_type": {
        "NO_MATCH": ONTOLOGY_NO_MATCH_DATA_TYPE,
        "AMBIGUOUS": ONTOLOGY_AMBIGUOUS_DATA_TYPE,
        "LOW_CONFIDENCE": ONTOLOGY_LOW_CONFIDENCE_DATA_TYPE,
    },
}


def _get_grounder(field: str):
    if field == "data_type" and _data_type_grounder is not None:
        return getattr(_data_type_grounder, "ground_data_type", None)
    if field == "tissue_type" and _tissue_type_grounder is not None:
        return getattr(_tissue_type_grounder, "ground_tissue_type", None)
    if field == "cell_line" and _cell_line_grounder is not None:
        return getattr(_cell_line_grounder, "ground_cell_line", None)
    if field == "disease" and _disease_grounder is not None:
        return getattr(_disease_grounder, "ground_disease", None)
    return None

def _resolve_ontology_source(field: str, config: Dict) -> str:
    if isinstance(config, dict):
        ontology_cfg = config.get("ontology") if isinstance(config.get("ontology"), dict) else None
        sources = None
        if isinstance(ontology_cfg, dict):
            sources = ontology_cfg.get("sources_by_field")
        if sources is None:
            sources = config.get("ontology_sources_by_field")
        if isinstance(sources, dict) and field in sources:
            return str(sources[field])
    return _DEFAULT_SOURCES_BY_FIELD.get(field, field)

def _make_none_match(field: str, raw_value: str, ontology: str) -> OntologyMatch:
    return OntologyMatch(
        field=field,
        raw_value=raw_value,
        ontology=ontology,
        status="NO_MATCH",
        matched_term_id=None,
        matched_label=None,
        matched_source=None,
        match_type="none",
        score=None,
        alternates=[],
    )

def _make_fallback_match(field: str, raw_value: str, ontology: str) -> OntologyMatch:
    return OntologyMatch(
        field=field,
        raw_value=raw_value,
        ontology=ontology,
        status="FALLBACK",
        matched_term_id=None,
        matched_label=None,
        matched_source=None,
        match_type="fallback",
        score=None,
        alternates=[],
    )

def _is_fallback_value(field: str, raw_value: str) -> bool:
    if field not in _FALLBACK_VALUES:
        return False
    return raw_value.strip().lower() in {
        value.lower() for value in _FALLBACK_VALUES[field]
    }


def _normalize_placeholder_value(value: str) -> str:
    normalized = _PLACEHOLDER_NORMALIZE_RE.sub(" ", (value or "").lower())
    return " ".join(normalized.split())


def _is_non_anatomical_tissue_placeholder(raw_value: str) -> bool:
    if not raw_value:
        return False
    return _normalize_placeholder_value(raw_value) in _NON_ANATOMICAL_TISSUE_PLACEHOLDERS


def _contains_explicit_disease_term(normalized_value: str) -> bool:
    if not normalized_value:
        return False
    tokens = set(normalized_value.split())
    return any(term in tokens for term in _DISEASE_EXPLICIT_TERMS)


def _is_disease_model_identifier(raw_value: str) -> bool:
    normalized = _normalize_placeholder_value(raw_value)
    if not normalized:
        return False
    tokens = set(normalized.split())
    has_identifier = any(token in _DISEASE_MODEL_IDENTIFIERS for token in tokens)
    has_phrase = any(phrase in normalized for phrase in _DISEASE_MODEL_PHRASES)
    if not (has_identifier or has_phrase):
        return False
    if _contains_explicit_disease_term(normalized):
        return False
    return True


def _make_placeholder_match(field: str, raw_value: str, ontology: str) -> OntologyMatch:
    return OntologyMatch(
        field=field,
        raw_value=raw_value,
        ontology=ontology,
        status="FALLBACK",
        matched_term_id=None,
        matched_label=None,
        matched_source=None,
        match_type="fallback",
        score=None,
        alternates=[],
        matched_via="non_anatomical_placeholder",
    )


def _make_disease_model_match(field: str, raw_value: str, ontology: str) -> OntologyMatch:
    return OntologyMatch(
        field=field,
        raw_value=raw_value,
        ontology=ontology,
        status="FALLBACK",
        matched_term_id=None,
        matched_label=None,
        matched_source=None,
        match_type="fallback",
        score=None,
        alternates=[],
        matched_via="model_identifier",
    )


def _normalize_allowlist_values(values: object) -> set[str]:
    if values is None:
        return set()
    if isinstance(values, str):
        items = [values]
    elif isinstance(values, (list, tuple, set)):
        items = list(values)
    else:
        return set()
    return {str(item).strip().lower() for item in items if str(item).strip()}


def _data_type_allowlist(config: Dict) -> set[str]:
    if not isinstance(config, dict):
        return set()
    ontology_cfg = (
        config.get("ontology")
        if isinstance(config.get("ontology"), dict)
        else None
    )
    if not isinstance(ontology_cfg, dict):
        return set()
    data_type_cfg = (
        ontology_cfg.get("data_type")
        if isinstance(ontology_cfg.get("data_type"), dict)
        else None
    )
    if not isinstance(data_type_cfg, dict):
        return set()
    enabled = bool(data_type_cfg.get("fallback_allowlist_enabled", False))
    if not enabled:
        return set()
    allowlist = data_type_cfg.get("fallback_allowlist")
    if allowlist is None:
        allowlist = data_type_cfg.get("allowlist")
    return _normalize_allowlist_values(allowlist)


def _is_data_type_allowlisted(raw_value: str, config: Dict) -> bool:
    if not raw_value:
        return False
    allowlist = _data_type_allowlist(config)
    if not allowlist:
        return False
    return raw_value.strip().lower() in allowlist

def _call_grounder(
    grounder_fn,
    raw_value: str,
    context_text: str,
    config: Dict,
):
    if grounder_fn is None:
        return None
    try:
        return grounder_fn(raw_value, context_text, config)
    except NotImplementedError:
        return None

def _failure_code_for_match(field: str, match: OntologyMatch) -> Optional[str]:
    if match.status == "INDEX_UNAVAILABLE":
        return ONTOLOGY_INDEX_UNAVAILABLE
    return _FIELD_FAILURE_CODES.get(field, {}).get(match.status)

def ground_all_fields(
    llm_output: Dict[str, str],
    context_text: str,
    ontology_config: Dict,
) -> tuple[Dict[str, OntologyMatch], Dict[str, str]]:
    """Ground ontology-driven fields and return matches with failure codes."""
    matches_by_field: Dict[str, OntologyMatch] = {}
    failures_by_field: Dict[str, str] = {}

    for field in ("data_type", "tissue_type", "cell_line", "disease"):
        raw_value = (llm_output.get(field) or "").strip()
        ontology = _resolve_ontology_source(field, ontology_config)

        if not raw_value:
            match = _make_none_match(field, raw_value, ontology)
        elif field == "tissue_type" and _is_non_anatomical_tissue_placeholder(raw_value):
            match = _make_placeholder_match(field, raw_value, ontology)
        elif field == "disease" and _is_disease_model_identifier(raw_value):
            match = _make_disease_model_match(field, raw_value, ontology)
        elif _is_fallback_value(field, raw_value):
            match = _make_fallback_match(field, raw_value, ontology)
        elif field == "data_type" and _is_data_type_allowlisted(raw_value, ontology_config):
            match = _make_fallback_match(field, raw_value, ontology)
        elif field == "cell_line" and is_cell_line_cell_type(raw_value):
            match = _make_fallback_match(field, raw_value, ontology)
        else:
            grounder_fn = _get_grounder(field)
            result = _call_grounder(
                grounder_fn,
                raw_value,
                context_text,
                ontology_config,
            )
            if isinstance(result, OntologyMatch):
                match = result
            else:
                match = _make_none_match(field, raw_value, ontology)

        matches_by_field[field] = match

        failure_code = _failure_code_for_match(field, match)
        if failure_code:
            failures_by_field[field] = failure_code

    return matches_by_field, failures_by_field
