"""Text snippets for UI guidance and tooltips."""

from __future__ import annotations

TABLE_GUIDANCE_TEXT = (
    "Hover cells for diagnostics. GSE/GSM accessions open GEO. "
    "Cell states: green=override, orange=blocking backend signal, blue=non-blocking signal, blue info marker=advisory signal."
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
CHECK_ALL_VISIBLE_TOOLTIP = "Mark all visible rows as checked (reviewed)."
UNCHECK_ALL_VISIBLE_TOOLTIP = "Clear the checked marker for all visible rows."
SAVE_OVERRIDES_TOOLTIP = "Persist current edits as curator overrides for this GSE."
REVERT_SELECTED_ROW_TOOLTIP = (
    "Undo session edits for the currently selected row "
    "(does not change saved overrides)."
)
CLEAR_ALL_EDITS_TOOLTIP = (
    "Undo all session edits for this GSE "
    "(does not change saved overrides)."
)
REVERT_TO_SAVED_TOOLTIP = (
    "Reload the last saved overrides (discard current session edits)."
)
CONFIRM_DISCARD_SAVED_OVERRIDES_TOOLTIP = (
    "Required confirmation before deleting saved overrides."
)
DISCARD_SAVED_OVERRIDES_TOOLTIP = (
    "Delete saved overrides for this GSE (irreversible)."
)
TABLE_HELP_LINES = (
    "Hover cells for diagnostics and backend context.",
    "GSE/GSM accessions link out to GEO.",
    "Cell colors: orange = blocking backend signal, green = curator override.",
    "Blue fill = non-blocking backend signal.",
    "Blue info marker + left accent = advisory signal (for example, GSE outliers).",
    "If overridden, green fill remains dominant and blocking/advisory remain visible as markers.",
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


def check_all_visible_tooltip() -> str:
    return CHECK_ALL_VISIBLE_TOOLTIP


def uncheck_all_visible_tooltip() -> str:
    return UNCHECK_ALL_VISIBLE_TOOLTIP


def save_overrides_tooltip() -> str:
    return SAVE_OVERRIDES_TOOLTIP


def revert_selected_row_tooltip() -> str:
    return REVERT_SELECTED_ROW_TOOLTIP


def clear_all_edits_tooltip() -> str:
    return CLEAR_ALL_EDITS_TOOLTIP


def revert_to_saved_tooltip() -> str:
    return REVERT_TO_SAVED_TOOLTIP


def confirm_discard_saved_overrides_tooltip() -> str:
    return CONFIRM_DISCARD_SAVED_OVERRIDES_TOOLTIP


def discard_saved_overrides_tooltip() -> str:
    return DISCARD_SAVED_OVERRIDES_TOOLTIP


__all__ = [
    "BULK_EDIT_TOOLTIP",
    "CHECK_ALL_VISIBLE_TOOLTIP",
    "CLEAR_ALL_EDITS_TOOLTIP",
    "CONFIRM_DISCARD_SAVED_OVERRIDES_TOOLTIP",
    "DISCARD_SAVED_OVERRIDES_TOOLTIP",
    "GSM_ACCESSION_TOOLTIP",
    "REVERT_SELECTED_ROW_TOOLTIP",
    "REVERT_TO_SAVED_TOOLTIP",
    "SAVE_OVERRIDES_TOOLTIP",
    "STATUS_ICON_TOOLTIP",
    "TABLE_LEGEND_TOOLTIP",
    "TABLE_GUIDANCE_TEXT",
    "TABLE_HELP_LINES",
    "UNCHECK_ALL_VISIBLE_TOOLTIP",
    "bulk_edit_tooltip",
    "check_all_visible_tooltip",
    "clear_all_edits_tooltip",
    "confirm_discard_saved_overrides_tooltip",
    "discard_saved_overrides_tooltip",
    "gsm_accession_tooltip",
    "revert_selected_row_tooltip",
    "revert_to_saved_tooltip",
    "save_overrides_tooltip",
    "status_icon_tooltip",
    "table_guidance_text",
    "table_help_lines",
    "table_legend_tooltip",
    "uncheck_all_visible_tooltip",
]
