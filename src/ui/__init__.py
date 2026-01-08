"""UI schema and loaders for review artifacts."""

from ui.loaders import (
    load_curation_jsonl,
    load_evidence_jsonl,
    load_jsonl,
    load_suggestions_jsonl_optional,
)
from ui.paths import InputPaths, resolve_input_paths
from ui.schema import (
    CANONICAL_FIELDS,
    CANONICAL_FIELDS_SET,
    CanonicalField,
    CurationFields,
    EvidenceRecord,
    NormalizedCurationRecord,
    SuggestionRecord,
)
from ui.state import (
    TableRow,
    build_table_rows,
    filter_table_rows,
    group_suggestions_by_field,
    index_curation_records,
    index_evidence_records,
    index_suggestion_records,
    lookup_evidence,
    lookup_suggestions,
)

__all__ = [
    "CANONICAL_FIELDS",
    "CANONICAL_FIELDS_SET",
    "CanonicalField",
    "CurationFields",
    "EvidenceRecord",
    "InputPaths",
    "NormalizedCurationRecord",
    "SuggestionRecord",
    "load_jsonl",
    "load_curation_jsonl",
    "load_evidence_jsonl",
    "load_suggestions_jsonl_optional",
    "TableRow",
    "build_table_rows",
    "filter_table_rows",
    "group_suggestions_by_field",
    "index_curation_records",
    "index_evidence_records",
    "index_suggestion_records",
    "lookup_evidence",
    "lookup_suggestions",
    "resolve_input_paths",
]
