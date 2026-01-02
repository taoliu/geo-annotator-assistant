from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Optional, List, Dict

@dataclass(frozen=True)
class OntologyCandidate:
    """A single ontology term candidate returned by RAG retrieval."""
    ontology: str
    term_id: str
    preferred_label: str
    score: float
    synonyms: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ontology": self.ontology,
            "term_id": self.term_id,
            "preferred_label": self.preferred_label,
            "synonyms": self.synonyms,
            "score": self.score,
            "metadata": self.metadata,
        }
