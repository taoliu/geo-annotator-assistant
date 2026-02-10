"""Styling helpers for the curator UI."""

from __future__ import annotations

import html

import pandas as pd

from ui.flags import FLAG_CATEGORY_COLORS, categorize_flag
from ui.schema import (
    CANONICAL_FIELDS,
    GSE_ACCESSION_RAW_COLUMN,
    GSM_ACCESSION_RAW_COLUMN,
)

_FLAGGED_CELL = "background-color: #ffe7cc"
_OVERRIDDEN_CELL = "background-color: #dff4df"
_OVERRIDDEN_FLAGGED_BORDER = "box-shadow: inset 0 0 0 2px #e47b00"
_HIGHLIGHT_ROW = "background-color: #f7f7f7"
_ACTIVE_ROW = "outline: 1px solid #4f6f90; outline-offset: -1px"
_GSM_ACCESSION_STYLE = (
    "color: #1a73e8; text-decoration: underline; cursor: pointer"
)
_STATUS_STYLE = "cursor: pointer; text-align: center; font-size: 1.05rem"
_FLAG_SUMMARY_COLUMN = "Flag summary"
_PRIMARY_FAILURE_COLUMN = "Primary failure"
_STATUS_COLUMN = "Status"
_REVIEW_FLAGS_COLUMN = "Review flags"
_TERMINAL_FALLBACK_COLUMN = "Terminal fallbacks"
_OUTLIER_COLUMN = "Outliers"
_CORE_FLAG_FIELDS = CANONICAL_FIELDS

_DECISION_FLAGGED = "background-color: #fde2e2"
_DECISION_ACCEPT = "background-color: #e9f7ef"
_REVIEW_BG = "background-color: #fff4e5"
_TERMINAL_BG = "background-color: #fde2e2"
_OUTLIER_BG = "background-color: #fff4e5"


def active_row_style(row_index: int, active_row_idx: int | None) -> str:
    if active_row_idx is None:
        return ""
    return _ACTIVE_ROW if row_index == active_row_idx else ""


def _normalize_accession(value: object) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    if "acc=" in value:
        return value.split("acc=", 1)[-1]
    return value


def style_curation_table(
    df: pd.DataFrame,
    flags_by_gsm: dict[tuple[str, str], dict[str, list[str]]],
    overridden_cells: set[tuple[str, str, str]] | None = None,
    active_row_idx: int | None = None,
    flag_summaries: dict[tuple[str, str], dict[str, object]] | None = None,
    primary_failures: dict[tuple[str, str], str] | None = None,
    enable_tooltips: bool = True,
) -> pd.io.formats.style.Styler:
    overridden_cells = overridden_cells or set()

    def _row_accessions(row: pd.Series) -> tuple[str | None, str | None]:
        gse = row.get(GSE_ACCESSION_RAW_COLUMN) or row.get("gse_accession")
        gsm = row.get(GSM_ACCESSION_RAW_COLUMN) or row.get("gsm_accession")
        return _normalize_accession(gse), _normalize_accession(gsm)

    def _style_row(row: pd.Series) -> list[str]:
        gse, gsm = _row_accessions(row)
        field_flags = {}
        if isinstance(gse, str) and isinstance(gsm, str):
            field_flags = flags_by_gsm.get((gse, gsm), {})
        flagged_fields = set(field_flags)
        row_has_flags = bool(field_flags)
        row_index = row.name if isinstance(row.name, int) else -1
        active_style = active_row_style(row_index, active_row_idx)

        summary_category = ""
        primary_failure = ""
        if isinstance(gse, str) and isinstance(gsm, str):
            if flag_summaries:
                summary = flag_summaries.get((gse, gsm))
                if isinstance(summary, dict):
                    highest = summary.get("highest")
                    if isinstance(highest, str):
                        summary_category = highest
            if primary_failures:
                primary_failure = primary_failures.get((gse, gsm), "")

        styles: list[str] = []
        for column in row.index:
            cell_styles: list[str] = []
            has_flags = column in _CORE_FLAG_FIELDS and column in flagged_fields
            has_override = (
                isinstance(gse, str)
                and isinstance(gsm, str)
                and column in CANONICAL_FIELDS
                and (gse, gsm, column) in overridden_cells
            )

            if has_override and has_flags:
                cell_styles.append(_OVERRIDDEN_CELL)
                cell_styles.append(_OVERRIDDEN_FLAGGED_BORDER)
            elif has_override:
                cell_styles.append(_OVERRIDDEN_CELL)
            elif has_flags:
                cell_styles.append(_FLAGGED_CELL)
            elif row_has_flags:
                cell_styles.append(_HIGHLIGHT_ROW)

            if active_style:
                cell_styles.append(active_style)

            if column == _PRIMARY_FAILURE_COLUMN and primary_failure:
                category = categorize_flag(primary_failure)
                color = FLAG_CATEGORY_COLORS.get(category)
                if color:
                    cell_styles.append(f"background-color: {color}")
                    cell_styles.append("font-weight: 600")
            if column == _FLAG_SUMMARY_COLUMN and summary_category:
                color = FLAG_CATEGORY_COLORS.get(summary_category)
                if color:
                    cell_styles.append(f"background-color: {color}")
                    cell_styles.append("font-weight: 600")
            if column == _STATUS_COLUMN:
                icon = str(row.get(_STATUS_COLUMN) or "")
                cell_styles.append(_STATUS_STYLE)
                if icon == "🚩":
                    cell_styles.append(_DECISION_FLAGGED)
                    cell_styles.append("font-weight: 600")
                elif icon == "✅":
                    cell_styles.append(_DECISION_ACCEPT)
            if column == _REVIEW_FLAGS_COLUMN:
                value = str(row.get(_REVIEW_FLAGS_COLUMN) or "")
                if value:
                    cell_styles.append(_REVIEW_BG)
            if column == _TERMINAL_FALLBACK_COLUMN:
                value = str(row.get(_TERMINAL_FALLBACK_COLUMN) or "")
                if value:
                    cell_styles.append(_TERMINAL_BG)
            if column == _OUTLIER_COLUMN:
                value = str(row.get(_OUTLIER_COLUMN) or "")
                if value:
                    cell_styles.append(_OUTLIER_BG)
            if column == "gsm_accession":
                cell_styles.append(_GSM_ACCESSION_STYLE)
            styles.append("; ".join(cell_styles))
        return styles

    styler = df.style.apply(_style_row, axis=1)
    if not enable_tooltips:
        return styler

    tooltip_df = pd.DataFrame("", index=df.index, columns=df.columns)
    if not df.empty:
        for row_idx, row in df.iterrows():
            gse, gsm = _row_accessions(row)
            if not (isinstance(gse, str) and isinstance(gsm, str)):
                continue
            field_flags = flags_by_gsm.get((gse, gsm), {})
            for field, flags in field_flags.items():
                if field not in _CORE_FLAG_FIELDS or not flags:
                    continue
                tooltip_df.at[row_idx, field] = html.escape(", ".join(flags), quote=True)

    if not tooltip_df.empty:
        styler = styler.set_tooltips(tooltip_df)
    return styler


__all__ = ["active_row_style", "style_curation_table"]
