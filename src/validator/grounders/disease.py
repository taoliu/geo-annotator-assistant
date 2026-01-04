"""Ontology grounding for disease."""

from __future__ import annotations

from typing import Any, Dict, Optional

from validator.grounders.ontology_grounder import ground_ontology_field
from validator.ontology_match import OntologyMatch


def ground_disease(
    raw_value: str,
    context_text: str,
    config: Optional[Dict[str, Any]],
) -> OntologyMatch:
    return ground_ontology_field(raw_value, context_text, config, field="disease")
