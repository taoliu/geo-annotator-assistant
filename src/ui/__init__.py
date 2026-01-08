"""UI schema and loaders for review artifacts."""

from ui.loaders import (
    load_curation_jsonl,
    load_evidence_jsonl,
    load_jsonl,
    load_suggestions_jsonl_optional,
)
from ui.schema import (
    CANONICAL_FIELDS,
    CANONICAL_FIELDS_SET,
    CanonicalField,
    CurationFields,
    EvidenceRecord,
    NormalizedCurationRecord,
    SuggestionRecord,
)

__all__ = [
    "CANONICAL_FIELDS",
    "CANONICAL_FIELDS_SET",
    "CanonicalField",
    "CurationFields",
    "EvidenceRecord",
    "NormalizedCurationRecord",
    "SuggestionRecord",
    "load_jsonl",
    "load_curation_jsonl",
    "load_evidence_jsonl",
    "load_suggestions_jsonl_optional",
]
