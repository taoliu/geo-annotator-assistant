"""Helpers for GSE dropdown workload/progress badges."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence


@dataclass(frozen=True)
class GseDropdownSummary:
    gse_accession: str
    flagged_count: int
    checked_count: int
    total_count: int


@dataclass(frozen=True)
class GseDropdownOptionModel:
    gse_accession: str
    flagged_count: int
    checked_count: int
    total_count: int
    flagged_ratio: str
    checked_ratio: str
    fallback_label: str


def build_gse_dropdown_summaries(
    curation_records: Sequence[dict],
    checked_state: Mapping[tuple[str, str], bool],
) -> dict[str, GseDropdownSummary]:
    totals: dict[str, int] = {}
    flagged: dict[str, int] = {}
    checked: dict[str, int] = {}
    loaded_keys: set[tuple[str, str]] = set()
    for record in curation_records:
        gse = record.get("gse_accession")
        gsm = record.get("gsm_accession")
        if not isinstance(gse, str) or not isinstance(gsm, str):
            continue
        loaded_keys.add((gse, gsm))
        totals[gse] = totals.get(gse, 0) + 1
        raw = record.get("raw")
        final_decision = raw.get("final_decision") if isinstance(raw, dict) else None
        if final_decision == "FLAGGED":
            flagged[gse] = flagged.get(gse, 0) + 1
    for (gse, gsm), is_checked in checked_state.items():
        if not is_checked:
            continue
        if (gse, gsm) not in loaded_keys:
            continue
        checked[gse] = checked.get(gse, 0) + 1

    summaries: dict[str, GseDropdownSummary] = {}
    for gse, total_count in totals.items():
        summaries[gse] = GseDropdownSummary(
            gse_accession=gse,
            flagged_count=flagged.get(gse, 0),
            checked_count=checked.get(gse, 0),
            total_count=total_count,
        )
    return summaries


def format_gse_dropdown_fallback(summary: GseDropdownSummary) -> str:
    flagged_ratio = f"{summary.flagged_count}/{summary.total_count}"
    checked_ratio = f"{summary.checked_count}/{summary.total_count}"
    return f"{summary.gse_accession} {flagged_ratio} {checked_ratio}"


def build_gse_dropdown_option_models(
    gse_options: Sequence[str],
    summaries: Mapping[str, GseDropdownSummary],
) -> list[GseDropdownOptionModel]:
    models: list[GseDropdownOptionModel] = []
    for gse in gse_options:
        summary = summaries.get(gse)
        if summary is None:
            summary = GseDropdownSummary(
                gse_accession=gse,
                flagged_count=0,
                checked_count=0,
                total_count=0,
            )
        model = GseDropdownOptionModel(
            gse_accession=gse,
            flagged_count=summary.flagged_count,
            checked_count=summary.checked_count,
            total_count=summary.total_count,
            flagged_ratio=f"{summary.flagged_count}/{summary.total_count}",
            checked_ratio=f"{summary.checked_count}/{summary.total_count}",
            fallback_label=format_gse_dropdown_fallback(summary),
        )
        models.append(model)
    return models


__all__ = [
    "GseDropdownSummary",
    "GseDropdownOptionModel",
    "build_gse_dropdown_summaries",
    "format_gse_dropdown_fallback",
    "build_gse_dropdown_option_models",
]
