"""Pure UI state helpers for filtering and lookups."""

from __future__ import annotations

from typing import Any, Iterable, TypedDict

from ui.schema import (
    CANONICAL_FIELDS,
    EvidenceRecord,
    NormalizedCurationRecord,
    SuggestionRecord,
)


class TableRow(TypedDict):
    gse_accession: str
    gsm_accession: str
    data_type: str
    organism: str
    tissue_type: str
    cell_line: str
    disease: str
    treatment: str


def build_table_rows(
    curation_records: Iterable[NormalizedCurationRecord],
) -> list[TableRow]:
    rows: list[TableRow] = []
    for record in curation_records:
        row: dict[str, Any] = {
            "gse_accession": record["gse_accession"],
            "gsm_accession": record["gsm_accession"],
        }
        for field in CANONICAL_FIELDS:
            row[field] = record["fields"][field]
        rows.append(row)  # type: ignore[arg-type]
    return rows


def filter_table_rows(
    rows: Iterable[TableRow],
    gse_filter: str | None,
    search_text: str | None,
) -> list[TableRow]:
    gse_filter_value = (gse_filter or "").strip()
    search_value = (search_text or "").strip().casefold()

    filtered: list[TableRow] = []
    for row in rows:
        if gse_filter_value and row["gse_accession"] != gse_filter_value:
            continue
        if search_value:
            if not _matches_search(row, search_value):
                continue
        filtered.append(row)
    return filtered


def _matches_search(row: TableRow, search_value: str) -> bool:
    candidates = [row["gsm_accession"]]
    for field in CANONICAL_FIELDS:
        candidates.append(row[field])
    for value in candidates:
        if search_value in value.casefold():
            return True
    return False


def index_curation_records(
    records: Iterable[NormalizedCurationRecord],
) -> dict[tuple[str, str], NormalizedCurationRecord]:
    lookup: dict[tuple[str, str], NormalizedCurationRecord] = {}
    for record in records:
        key = (record["gse_accession"], record["gsm_accession"])
        lookup[key] = record
    return lookup


def index_evidence_records(
    records: Iterable[EvidenceRecord],
) -> dict[tuple[str, str], EvidenceRecord]:
    lookup: dict[tuple[str, str], EvidenceRecord] = {}
    for record in records:
        key = (record["gse_accession"], record["gsm_accession"])
        lookup[key] = record
    return lookup


def index_suggestion_records(
    records: Iterable[SuggestionRecord],
) -> dict[tuple[str, str], list[SuggestionRecord]]:
    lookup: dict[tuple[str, str], list[SuggestionRecord]] = {}
    for record in records:
        key = (record["gse_accession"], record["gsm_accession"])
        lookup.setdefault(key, []).append(record)
    return lookup


def lookup_evidence(
    lookup: dict[tuple[str, str], EvidenceRecord],
    gse_accession: str,
    gsm_accession: str,
) -> EvidenceRecord | None:
    return lookup.get((gse_accession, gsm_accession))


def lookup_suggestions(
    lookup: dict[tuple[str, str], list[SuggestionRecord]],
    gse_accession: str,
    gsm_accession: str,
) -> list[SuggestionRecord]:
    return list(lookup.get((gse_accession, gsm_accession), []))


def group_suggestions_by_field(
    records: Iterable[SuggestionRecord],
) -> list[tuple[str, list[SuggestionRecord]]]:
    grouped: dict[str, list[SuggestionRecord]] = {}
    for record in records:
        grouped.setdefault(record["field"], []).append(record)
    return [(field, grouped[field]) for field in sorted(grouped)]


__all__ = [
    "TableRow",
    "build_table_rows",
    "filter_table_rows",
    "index_curation_records",
    "index_evidence_records",
    "index_suggestion_records",
    "lookup_evidence",
    "lookup_suggestions",
    "group_suggestions_by_field",
]
