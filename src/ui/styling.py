"""Styling helpers for the curator UI."""

from __future__ import annotations

import pandas as pd

from ui.schema import CANONICAL_FIELDS

_HIGHLIGHT_CELL = "background-color: #fff3cd"
_HIGHLIGHT_ROW = "background-color: #f7f7f7"


def style_curation_table(
    df: pd.DataFrame,
    flags_by_gsm: dict[tuple[str, str], dict[str, list[str]]],
) -> pd.io.formats.style.Styler:
    def _style_row(row: pd.Series) -> list[str]:
        gse = row.get("gse_accession")
        gsm = row.get("gsm_accession")
        flagged_fields = set()
        if isinstance(gse, str) and isinstance(gsm, str):
            flagged_fields = set(flags_by_gsm.get((gse, gsm), {}))
        row_has_flags = bool(flagged_fields)

        styles: list[str] = []
        for column in row.index:
            if column in CANONICAL_FIELDS and column in flagged_fields:
                styles.append(_HIGHLIGHT_CELL)
            elif row_has_flags:
                styles.append(_HIGHLIGHT_ROW)
            else:
                styles.append("")
        return styles

    return df.style.apply(_style_row, axis=1)


__all__ = ["style_curation_table"]
