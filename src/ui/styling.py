"""Styling helpers for the curator UI."""

from __future__ import annotations

import pandas as pd

from ui.schema import CANONICAL_FIELDS

_HIGHLIGHT_CELL = "background-color: #fff3cd"
_HIGHLIGHT_ROW = "background-color: #f7f7f7"
_ACTIVE_ROW = "background-color: #e8f4ff"
_GSM_ACCESSION_STYLE = (
    "color: #1a73e8; text-decoration: underline; cursor: pointer"
)


def active_row_style(row_index: int, active_row_idx: int | None) -> str:
    if active_row_idx is None:
        return ""
    return _ACTIVE_ROW if row_index == active_row_idx else ""


def style_curation_table(
    df: pd.DataFrame,
    flags_by_gsm: dict[tuple[str, str], dict[str, list[str]]],
    active_row_idx: int | None = None,
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

        styles: list[str] = []
        for column in row.index:
            cell_styles: list[str] = []
            if column in CANONICAL_FIELDS and column in flagged_fields:
                cell_styles.append(_HIGHLIGHT_CELL)
            elif active_style:
                cell_styles.append(active_style)
            elif row_has_flags:
                cell_styles.append(_HIGHLIGHT_ROW)
            if column == "gsm_accession":
                cell_styles.append(_GSM_ACCESSION_STYLE)
            styles.append("; ".join(cell_styles))
        return styles

    return df.style.apply(_style_row, axis=1)


__all__ = ["active_row_style", "style_curation_table"]
