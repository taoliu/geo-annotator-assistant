"""UI-facing schemas for review artifacts."""

from __future__ import annotations

from typing import Any, Literal, TypedDict

CANONICAL_FIELDS: tuple[str, ...] = (
    "data_type",
    "organism",
    "tissue_type",
    "cell_line",
    "disease",
    "treatment",
)
CANONICAL_FIELDS_SET = set(CANONICAL_FIELDS)

CanonicalField = Literal[
    "data_type",
    "organism",
    "tissue_type",
    "cell_line",
    "disease",
    "treatment",
]


class CurationFields(TypedDict):
    data_type: str
    organism: str
    tissue_type: str
    cell_line: str
    disease: str
    treatment: str


class NormalizedCurationRecord(TypedDict):
    gse_accession: str
    gsm_accession: str
    fields: CurationFields
    raw: dict[str, Any]


class EvidenceRecord(TypedDict):
    gse_accession: str
    gsm_accession: str
    raw: dict[str, Any]


class AuditRecord(TypedDict):
    gse_accession: str
    gsm_accession: str
    raw: dict[str, Any]


class SuggestionRecord(TypedDict):
    gse_accession: str
    gsm_accession: str
    field: CanonicalField
    raw: dict[str, Any]


__all__ = [
    "CANONICAL_FIELDS",
    "CANONICAL_FIELDS_SET",
    "CanonicalField",
    "CurationFields",
    "NormalizedCurationRecord",
    "EvidenceRecord",
    "AuditRecord",
    "SuggestionRecord",
]
