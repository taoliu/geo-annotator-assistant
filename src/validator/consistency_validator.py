from __future__ import annotations
from typing import Dict, List

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

def consistency_validate(parsed_output: Dict[str, str], context_text: str) -> List[str]:
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
        if any(k in ctx for k in _DISEASE_KEYWORDS):
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
