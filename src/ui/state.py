"""Pure UI state helpers for filtering and lookups."""

from __future__ import annotations

from typing import Any, Iterable, Mapping, Sequence, TypedDict

from ui.schema import (
    CANONICAL_FIELDS,
    AuditRecord,
    EvidenceRecord,
    NormalizedCurationRecord,
    SuggestionRecord,
)
from ui.overrides import (
    OverrideKey,
    OverrideValue,
    OverridesForGsm,
    apply_overrides_to_record,
    overrides_for_gsm,
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


SelectionKey = tuple[str, str]


class ModalState(TypedDict):
    active: SelectionKey | None
    is_open: bool


class DetailsContext(TypedDict):
    selection_key: SelectionKey
    evidence: EvidenceRecord | None
    audit: AuditRecord | None
    suggestions: list[SuggestionRecord]
    flagged_fields: dict[str, list[str]]
    curation: NormalizedCurationRecord | None
    selected_overrides: OverridesForGsm
    effective_fields: dict[str, OverrideValue] | None


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


def index_audit_records(
    records: Iterable[AuditRecord],
) -> dict[tuple[str, str], AuditRecord]:
    lookup: dict[tuple[str, str], AuditRecord] = {}
    for record in records:
        key = (record["gse_accession"], record["gsm_accession"])
        lookup[key] = record
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


def lookup_audit(
    lookup: dict[tuple[str, str], AuditRecord],
    gse_accession: str,
    gsm_accession: str,
) -> AuditRecord | None:
    return lookup.get((gse_accession, gsm_accession))


def group_suggestions_by_field(
    records: Iterable[SuggestionRecord],
) -> list[tuple[str, list[SuggestionRecord]]]:
    grouped: dict[str, list[SuggestionRecord]] = {}
    for record in records:
        grouped.setdefault(record["field"], []).append(record)
    return [(field, grouped[field]) for field in sorted(grouped)]


def default_modal_state() -> ModalState:
    return {"active": None, "is_open": False}


def update_modal_state(
    state: ModalState,
    selected_key: SelectionKey | None,
) -> ModalState:
    if selected_key is None:
        return state
    return {"active": selected_key, "is_open": True}


def close_modal(state: ModalState) -> ModalState:
    if not state["is_open"]:
        return state
    return {"active": state["active"], "is_open": False}


def resolve_selected_key(
    rows: Sequence[TableRow],
    selected_rows: Sequence[int] | None,
) -> SelectionKey | None:
    if not selected_rows:
        return None
    index = selected_rows[0]
    if index < 0 or index >= len(rows):
        return None
    row = rows[index]
    return (row["gse_accession"], row["gsm_accession"])


def details_render_mode() -> str:
    return "modal"


def build_details_context(
    selection_key: SelectionKey,
    curation_lookup: dict[SelectionKey, NormalizedCurationRecord],
    evidence_lookup: dict[SelectionKey, EvidenceRecord],
    audit_lookup: dict[SelectionKey, AuditRecord],
    suggestions_lookup: dict[SelectionKey, list[SuggestionRecord]],
    flags_by_gsm: dict[SelectionKey, dict[str, list[str]]],
    overrides: Mapping[OverrideKey, OverrideValue],
) -> DetailsContext:
    evidence = lookup_evidence(
        evidence_lookup, selection_key[0], selection_key[1]
    )
    audit = lookup_audit(
        audit_lookup, selection_key[0], selection_key[1]
    )
    suggestions = lookup_suggestions(
        suggestions_lookup, selection_key[0], selection_key[1]
    )
    flagged_fields = flags_by_gsm.get(selection_key, {})
    curation = curation_lookup.get(selection_key)
    selected_overrides = overrides_for_gsm(
        overrides, selection_key[0], selection_key[1]
    )
    effective_fields = apply_overrides_to_record(curation, selected_overrides)
    return {
        "selection_key": selection_key,
        "evidence": evidence,
        "audit": audit,
        "suggestions": suggestions,
        "flagged_fields": flagged_fields,
        "curation": curation,
        "selected_overrides": selected_overrides,
        "effective_fields": effective_fields,
    }


__all__ = [
    "SelectionKey",
    "ModalState",
    "DetailsContext",
    "TableRow",
    "build_table_rows",
    "filter_table_rows",
    "index_curation_records",
    "index_evidence_records",
    "index_audit_records",
    "index_suggestion_records",
    "lookup_evidence",
    "lookup_audit",
    "lookup_suggestions",
    "group_suggestions_by_field",
    "default_modal_state",
    "update_modal_state",
    "close_modal",
    "resolve_selected_key",
    "details_render_mode",
    "build_details_context",
]
