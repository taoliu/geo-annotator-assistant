"""Text snippets for UI guidance and tooltips."""

from __future__ import annotations

TABLE_GUIDANCE_TEXT = (
    "Hover cells for diagnostics. GSE/GSM accessions open GEO. "
    "Cell states: green=override, orange=backend flag, green+orange border=both."
)
GSM_ACCESSION_TOOLTIP = "Open GEO page"
STATUS_ICON_TOOLTIP = "Decision status (✅ = ACCEPT, 🚩 = FLAGGED)"
TABLE_LEGEND_TOOLTIP = (
    "Status: row state (flagged/clean). "
    "Checked: curator review marker saved to disk. "
    "Edited: pencil indicates curator overrides. "
    "Details via hover tooltips."
)
BULK_EDIT_TOOLTIP = (
    "Apply one value to one column across selected rows. "
    "This operation is explicit, reversible, and UI-only."
)
TABLE_HELP_LINES = (
    "Hover cells for diagnostics and backend context.",
    "GSE/GSM accessions link out to GEO.",
    "Cell colors: orange = backend evidence flag, green = curator override.",
    "If both apply, green fill is kept and an orange border is added.",
    "Edits are session-only until you export overrides.",
)


def table_guidance_text() -> str:
    return TABLE_GUIDANCE_TEXT


def table_help_lines() -> tuple[str, ...]:
    return TABLE_HELP_LINES


def gsm_accession_tooltip() -> str:
    return GSM_ACCESSION_TOOLTIP


def status_icon_tooltip() -> str:
    return STATUS_ICON_TOOLTIP


def table_legend_tooltip() -> str:
    return TABLE_LEGEND_TOOLTIP


def bulk_edit_tooltip() -> str:
    return BULK_EDIT_TOOLTIP


__all__ = [
    "BULK_EDIT_TOOLTIP",
    "GSM_ACCESSION_TOOLTIP",
    "STATUS_ICON_TOOLTIP",
    "TABLE_LEGEND_TOOLTIP",
    "TABLE_GUIDANCE_TEXT",
    "TABLE_HELP_LINES",
    "bulk_edit_tooltip",
    "gsm_accession_tooltip",
    "status_icon_tooltip",
    "table_guidance_text",
    "table_help_lines",
    "table_legend_tooltip",
]
