"""Styling helpers for the curator UI."""

from __future__ import annotations

import pandas as pd

from ui.flags import FLAG_CATEGORY_COLORS, categorize_flag
from ui.schema import CANONICAL_FIELDS

_HIGHLIGHT_CELL = "background-color: #fff3cd"
_HIGHLIGHT_ROW = "background-color: #f7f7f7"
_ACTIVE_ROW = "background-color: #e8f4ff"
_GSM_ACCESSION_STYLE = (
    "color: #1a73e8; text-decoration: underline; cursor: pointer"
)
_FLAG_SUMMARY_COLUMN = "Flag summary"
_PRIMARY_FAILURE_COLUMN = "Primary failure"
_DECISION_COLUMN = "Decision"
_REVIEW_FLAGS_COLUMN = "Review flags"
_TERMINAL_FALLBACK_COLUMN = "Terminal fallbacks"
_OUTLIER_COLUMN = "Outliers"

_DECISION_FLAGGED = "background-color: #fde2e2"
_DECISION_ACCEPT = "background-color: #e9f7ef"
_REVIEW_BG = "background-color: #fff4e5"
_TERMINAL_BG = "background-color: #fde2e2"
_OUTLIER_BG = "background-color: #fff4e5"


def active_row_style(row_index: int, active_row_idx: int | None) -> str:
    if active_row_idx is None:
        return ""
    return _ACTIVE_ROW if row_index == active_row_idx else ""


def style_curation_table(
    df: pd.DataFrame,
    flags_by_gsm: dict[tuple[str, str], dict[str, list[str]]],
    active_row_idx: int | None = None,
    flag_summaries: dict[tuple[str, str], dict[str, object]] | None = None,
    primary_failures: dict[tuple[str, str], str] | None = None,
) -> pd.io.formats.style.Styler:
    def _style_row(row: pd.Series) -> list[str]:
        gse = row.get("gse_accession")
        gsm = row.get("gsm_accession")
        flagged_fields = set()
        if isinstance(gse, str) and isinstance(gsm, str):
            flagged_fields = set(flags_by_gsm.get((gse, gsm), {}))
        row_has_flags = bool(flagged_fields)
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
            if column in CANONICAL_FIELDS and column in flagged_fields:
                cell_styles.append(_HIGHLIGHT_CELL)
            elif active_style:
                cell_styles.append(active_style)
            elif row_has_flags:
                cell_styles.append(_HIGHLIGHT_ROW)
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
            if column == _DECISION_COLUMN:
                decision = str(row.get(_DECISION_COLUMN) or "")
                if decision == "FLAGGED":
                    cell_styles.append(_DECISION_FLAGGED)
                    cell_styles.append("font-weight: 600")
                elif decision == "ACCEPT":
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

    return df.style.apply(_style_row, axis=1)


__all__ = ["active_row_style", "style_curation_table"]
