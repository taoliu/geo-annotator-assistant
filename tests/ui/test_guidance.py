from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ui.help_text import (
    bulk_edit_tooltip,
    check_all_visible_tooltip,
    clear_all_edits_tooltip,
    confirm_discard_saved_overrides_tooltip,
    discard_saved_overrides_tooltip,
    gsm_accession_tooltip,
    revert_selected_row_tooltip,
    revert_to_saved_tooltip,
    save_overrides_tooltip,
    table_guidance_text,
    table_help_lines,
    table_legend_tooltip,
    uncheck_all_visible_tooltip,
)


def test_table_guidance_text_mentions_accession() -> None:
    text = table_guidance_text()

    assert "GSM" in text
    assert "GEO" in text
    assert "hover" in text.casefold() or "tooltip" in text.casefold()
    assert "green" in text.casefold()
    assert "orange" in text.casefold()
    assert "blue" in text.casefold()
    assert "non-blocking" in text.casefold()


def test_table_help_lines_include_session_only() -> None:
    lines = table_help_lines()

    assert any("session-only" in line for line in lines)
    assert any("orange" in line.casefold() and "green" in line.casefold() for line in lines)
    assert any("blue fill" in line.casefold() and "non-blocking" in line.casefold() for line in lines)
    assert any("advisory" in line.casefold() and "marker" in line.casefold() for line in lines)
    assert any(
        "hover" in line.casefold()
        or "diagnostic" in line.casefold()
        or "tooltip" in line.casefold()
        for line in lines
    )
    assert gsm_accession_tooltip() == "Open GEO page"


def test_table_legend_tooltip_text() -> None:
    tooltip = table_legend_tooltip()

    assert "Status: row state (flagged/clean)." in tooltip
    assert "Checked: curator review marker saved to disk." in tooltip
    assert "Edited: pencil indicates curator overrides." in tooltip
    assert "Details via hover tooltips." in tooltip


def test_bulk_edit_tooltip_text() -> None:
    tooltip = bulk_edit_tooltip()

    assert "Apply one value to one column across selected rows." in tooltip
    assert "This operation is explicit, reversible, and UI-only." in tooltip


def test_curator_action_tooltips_text() -> None:
    assert check_all_visible_tooltip() == "Mark all visible rows as checked (reviewed)."
    assert uncheck_all_visible_tooltip() == "Clear the checked marker for all visible rows."
    assert (
        save_overrides_tooltip()
        == "Persist current edits as curator overrides for this GSE."
    )
    assert (
        revert_selected_row_tooltip()
        == "Undo session edits for the currently selected row (does not change saved overrides)."
    )
    assert (
        clear_all_edits_tooltip()
        == "Undo all session edits for this GSE (does not change saved overrides)."
    )
    assert (
        revert_to_saved_tooltip()
        == "Reload the last saved overrides (discard current session edits)."
    )
    assert (
        confirm_discard_saved_overrides_tooltip()
        == "Required confirmation before deleting saved overrides."
    )
    assert (
        discard_saved_overrides_tooltip()
        == "Delete saved overrides for this GSE (irreversible)."
    )
