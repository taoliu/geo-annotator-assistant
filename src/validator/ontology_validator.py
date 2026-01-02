from __future__ import annotations

from typing import Dict, Optional, Tuple

from validator.ontology_match import OntologyMatch
from validator.thresholds import is_match_acceptable

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

ONTOLOGY_NO_MATCH = "ontology_no_match"
ONTOLOGY_LOW_SCORE = "ontology_low_score"

_FIELD_TO_ONTOLOGY = {
    "data_type": "EFO",
    "tissue_type": "UBERON",
    "cell_line": "CELLOSAURUS",
    "disease": "DOID",
}

_FALLBACK_VALUES = {
    "tissue_type": "Unknown",
    "cell_line": "No",
    "disease": "Healthy",
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

def _resolve_ontology_and_collection(field: str, rag_config: Dict) -> Tuple[str, Optional[str]]:
    ontology = _FIELD_TO_ONTOLOGY.get(field, field)
    collections = rag_config.get("collections") if isinstance(rag_config, dict) else None
    collection_name: Optional[str] = None
    if isinstance(collections, dict):
        if ontology in collections:
            collection_name = collections[ontology]
        elif field in collections:
            ontology = field
            collection_name = collections[field]
    return ontology, collection_name

def _make_none_match(field: str, raw_value: str, ontology: str) -> OntologyMatch:
    return OntologyMatch(
        field=field,
        raw_value=raw_value,
        ontology=ontology,
        matched_term_id=None,
        matched_label=None,
        match_type="none",
        score=None,
    )

def _make_fallback_match(field: str, raw_value: str, ontology: str) -> OntologyMatch:
    return OntologyMatch(
        field=field,
        raw_value=raw_value,
        ontology=ontology,
        matched_term_id=None,
        matched_label=None,
        match_type="fallback",
        score=None,
    )

def _is_fallback_value(field: str, raw_value: str) -> bool:
    if field not in _FALLBACK_VALUES:
        return False
    return raw_value.strip().lower() == _FALLBACK_VALUES[field].lower()

def _call_grounder(
    grounder_fn,
    raw_value: str,
    context_text: str,
    persist_path: Optional[str],
    collection_name: Optional[str],
    k: int,
):
    if grounder_fn is None:
        return None
    try:
        return grounder_fn(raw_value, context_text, persist_path, collection_name, k)
    except NotImplementedError:
        return None

def ground_all_fields(
    llm_output: Dict[str, str],
    context_text: str,
    rag_config: Dict,
) -> Tuple[Dict[str, OntologyMatch], Dict[str, str]]:
    """Ground ontology-driven fields and return matches with failure codes."""
    matches_by_field: Dict[str, OntologyMatch] = {}
    failures_by_field: Dict[str, str] = {}

    thresholds_cfg = rag_config.get("thresholds") if isinstance(rag_config, dict) else None
    persist_path = rag_config.get("persist_path") if isinstance(rag_config, dict) else None
    k = rag_config.get("k", 10) if isinstance(rag_config, dict) else 10

    for field in ("data_type", "tissue_type", "cell_line", "disease"):
        raw_value = (llm_output.get(field) or "").strip()
        ontology, collection_name = _resolve_ontology_and_collection(field, rag_config)

        if not raw_value:
            match = _make_none_match(field, raw_value, ontology)
        elif _is_fallback_value(field, raw_value):
            match = _make_fallback_match(field, raw_value, ontology)
        else:
            grounder_fn = _get_grounder(field)
            result = _call_grounder(
                grounder_fn,
                raw_value,
                context_text,
                persist_path,
                collection_name,
                k,
            )
            if isinstance(result, OntologyMatch):
                match = result
            else:
                match = _make_none_match(field, raw_value, ontology)

        matches_by_field[field] = match

        if not is_match_acceptable(field, match, thresholds_cfg):
            if match.match_type == "none" or match.score is None:
                failures_by_field[field] = ONTOLOGY_NO_MATCH
            else:
                failures_by_field[field] = ONTOLOGY_LOW_SCORE

    return matches_by_field, failures_by_field
