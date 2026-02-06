"""Text snippets for UI guidance and tooltips."""

from __future__ import annotations

TABLE_GUIDANCE_TEXT = (
    "Hover cells for diagnostics. GSE/GSM accessions open GEO."
)
GSM_ACCESSION_TOOLTIP = "Open GEO page"
STATUS_ICON_TOOLTIP = "Decision status (✅ = ACCEPT, 🚩 = FLAGGED)"
TABLE_HELP_LINES = (
    "Hover cells for diagnostics and backend context.",
    "GSE/GSM accessions link out to GEO.",
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


__all__ = [
    "GSM_ACCESSION_TOOLTIP",
    "STATUS_ICON_TOOLTIP",
    "TABLE_GUIDANCE_TEXT",
    "TABLE_HELP_LINES",
    "gsm_accession_tooltip",
    "status_icon_tooltip",
    "table_guidance_text",
    "table_help_lines",
]
