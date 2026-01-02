from __future__ import annotations

from typing import Dict, Optional

from validator.ontology_match import OntologyMatch

_DEFAULT_THRESHOLDS: Dict[str, float] = {
    "data_type": 0.75,
    "tissue_type": 0.75,
    "cell_line": 0.80,
    "disease": 0.75,
}

def get_threshold(field: str, thresholds_cfg: Optional[Dict[str, float]] = None) -> float:
    """Return the score threshold for a given field."""
    if thresholds_cfg and field in thresholds_cfg:
        try:
            return float(thresholds_cfg[field])
        except (TypeError, ValueError):
            return _DEFAULT_THRESHOLDS.get(field, 0.75)
    return _DEFAULT_THRESHOLDS.get(field, 0.75)

def is_match_acceptable(
    field: str,
    match: OntologyMatch,
    thresholds_cfg: Optional[Dict[str, float]] = None,
) -> bool:
    """Return True if the match is acceptable for the field threshold."""
    if match.match_type == "fallback":
        return True
    if match.match_type == "none":
        return False
    if match.score is None:
        return False
    return match.score >= get_threshold(field, thresholds_cfg)
