from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Optional

_ALLOWED_MATCH_TYPES = {"exact", "synonym", "fuzzy", "none", "fallback"}

@dataclass(frozen=True)
class OntologyMatch:
    field: str
    raw_value: str
    ontology: str
    matched_term_id: Optional[str]
    matched_label: Optional[str]
    match_type: str
    score: Optional[float]

    def __post_init__(self):
        if self.match_type not in _ALLOWED_MATCH_TYPES:
            raise ValueError(f"Invalid match_type: {self.match_type}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "field": self.field,
            "raw_value": self.raw_value,
            "ontology": self.ontology,
            "matched_term_id": self.matched_term_id,
            "matched_label": self.matched_label,
            "match_type": self.match_type,
            "score": self.score,
        }
