"""Field-level flag extraction for UI highlighting."""

from __future__ import annotations

from typing import Any, Iterable

from ui.schema import CANONICAL_FIELDS, EvidenceRecord


def extract_field_flags(evidence_raw: dict[str, Any]) -> dict[str, list[str]]:
    """Extract per-field flags from evidence.

    Signals considered (by field):
    - evidence_by_field[<field>]["flags"] (list[str])
    - evidence_by_field[<field>]["terminal_fallback"] == True -> "terminal_fallback"
    - evidence_by_field[<field>]["ontology_status"] and != "MATCHED"
      -> "ontology_status:<STATUS>"
    """
    if not isinstance(evidence_raw, dict):
        return {}
    evidence_by_field = evidence_raw.get("evidence_by_field")
    if not isinstance(evidence_by_field, dict):
        return {}

    flags_by_field: dict[str, list[str]] = {}
    for field in CANONICAL_FIELDS:
        field_evidence = evidence_by_field.get(field)
        if not isinstance(field_evidence, dict):
            continue
        tags: list[str] = []
        raw_flags = field_evidence.get("flags")
        if isinstance(raw_flags, list):
            for flag in raw_flags:
                if isinstance(flag, str) and flag:
                    tags.append(flag)
        if field_evidence.get("terminal_fallback") is True:
            tags.append("terminal_fallback")
        ontology_status = field_evidence.get("ontology_status")
        if isinstance(ontology_status, str) and ontology_status:
            if ontology_status != "MATCHED":
                tags.append(f"ontology_status:{ontology_status}")

        if tags:
            flags_by_field[field] = _dedupe_sorted(tags)

    return flags_by_field


def build_flags_index(
    evidence_records: Iterable[EvidenceRecord],
) -> dict[tuple[str, str], dict[str, list[str]]]:
    flags_by_gsm: dict[tuple[str, str], dict[str, list[str]]] = {}
    for record in evidence_records:
        gse = record.get("gse_accession")
        gsm = record.get("gsm_accession")
        if not gse or not gsm:
            continue
        field_flags = extract_field_flags(record.get("raw", {}))
        if field_flags:
            flags_by_gsm[(gse, gsm)] = field_flags
    return flags_by_gsm


def _dedupe_sorted(items: list[str]) -> list[str]:
    return sorted(set(items))


__all__ = ["extract_field_flags", "build_flags_index"]
