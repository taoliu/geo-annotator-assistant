"""Text snippets for UI guidance and tooltips."""

from __future__ import annotations

TABLE_GUIDANCE_TEXT = "Click a GSM accession to open details."
GSM_ACCESSION_TOOLTIP = "Open details"
TABLE_HELP_LINES = (
    "Click a GSM accession row to open details in the modal.",
    "Use the Close button in the modal to dismiss it.",
    "Edits are session-only until you export overrides.",
)


def table_guidance_text() -> str:
    return TABLE_GUIDANCE_TEXT


def table_help_lines() -> tuple[str, ...]:
    return TABLE_HELP_LINES


def gsm_accession_tooltip() -> str:
    return GSM_ACCESSION_TOOLTIP


__all__ = [
    "GSM_ACCESSION_TOOLTIP",
    "TABLE_GUIDANCE_TEXT",
    "TABLE_HELP_LINES",
    "gsm_accession_tooltip",
    "table_guidance_text",
    "table_help_lines",
]
