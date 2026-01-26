from __future__ import annotations
from typing import Dict, List, Optional, Any
import re

from validator.heuristics import get_heuristics

ASSAY_PLATFORM_CONFLICT = "assay_platform_conflict"
SINGLE_CELL_EVIDENCE_MISSING = "single_cell_evidence_missing"
HEALTHY_DISEASE_CONFLICT = "healthy_disease_conflict"
ORGANISM_CONTEXT_CONFLICT = "organism_context_conflict"

_HEURISTICS = get_heuristics()
_CONSISTENCY = _HEURISTICS["consistency"]

_SINGLE_CELL_DATA_TYPES = {dt.lower() for dt in _CONSISTENCY["single_cell_data_types"]}
_SINGLE_CELL_KEYWORDS = [kw.lower() for kw in _CONSISTENCY["single_cell_keywords"]]
_MICROARRAY_DATA_TYPE = _CONSISTENCY["microarray_data_type"].lower()
_SEQUENCING_KEYWORDS = [kw.lower() for kw in _CONSISTENCY["sequencing_keywords"]]
_HEALTHY_VALUE = _CONSISTENCY["healthy_value"].lower()
_DISEASE_KEYWORDS = [kw.lower() for kw in _CONSISTENCY["disease_keywords"]]
_ORGANISM_CONFLICTS = _CONSISTENCY["organism_conflicts"]
_DISEASE_LABEL_RE = re.compile(r"\bdisease(?:\s*state)?\b\s*[:=]\s*([^\n;]+)", re.IGNORECASE)
_DISEASE_LABEL_IGNORE = {
    "healthy",
    "none",
    "normal",
    "control",
    "vehicle",
    "na",
    "n/a",
    "unknown",
}


def _has_explicit_disease_terms(ctx: str) -> bool:
    for keyword in _DISEASE_KEYWORDS:
        if keyword == "disease:":
            continue
        if keyword in ctx:
            return True
    match = _DISEASE_LABEL_RE.search(ctx)
    if match:
        value = match.group(1).strip().lower()
        if value and not any(token in value for token in _DISEASE_LABEL_IGNORE):
            return True
    return False


def _has_ontology_disease_match(ontology_matches: Optional[Dict[str, Any]]) -> bool:
    if not isinstance(ontology_matches, dict):
        return False
    match = ontology_matches.get("disease")
    if not match:
        return False
    if isinstance(match, dict):
        status = match.get("status")
        label = match.get("matched_label")
    else:
        status = getattr(match, "status", None)
        label = getattr(match, "matched_label", None)
    if str(status or "").upper() != "MATCHED":
        return False
    if label is None:
        return False
    return str(label).strip().lower() != _HEALTHY_VALUE

def consistency_validate(
    parsed_output: Dict[str, str],
    context_text: str,
    *,
    ontology_matches: Optional[Dict[str, Any]] = None,
) -> List[str]:
    """Keyword-based cross-field consistency checks."""
    flags: List[str] = []
    ctx = context_text.lower()

    dt = parsed_output.get("data_type", "").lower()
    if dt in _SINGLE_CELL_DATA_TYPES:
        if not any(k in ctx for k in _SINGLE_CELL_KEYWORDS):
            flags.append(SINGLE_CELL_EVIDENCE_MISSING)

    if dt == _MICROARRAY_DATA_TYPE:
        if any(k in ctx for k in _SEQUENCING_KEYWORDS):
            flags.append(ASSAY_PLATFORM_CONFLICT)

    disease = parsed_output.get("disease", "").lower()
    if disease == _HEALTHY_VALUE:
        if _has_explicit_disease_terms(ctx) or _has_ontology_disease_match(ontology_matches):
            flags.append(HEALTHY_DISEASE_CONFLICT)

    org = parsed_output.get("organism", "").lower()
    if org:
        for first, second in _ORGANISM_CONFLICTS:
            first_lower = first.lower()
            second_lower = second.lower()
            if first_lower in org and second_lower in ctx:
                flags.append(ORGANISM_CONTEXT_CONFLICT)
            if second_lower in org and first_lower in ctx:
                flags.append(ORGANISM_CONTEXT_CONFLICT)

    return sorted(set(flags))
