from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ui.help_text import (
    bulk_edit_tooltip,
    gsm_accession_tooltip,
    table_guidance_text,
    table_help_lines,
    table_legend_tooltip,
)


def test_table_guidance_text_mentions_accession() -> None:
    text = table_guidance_text()

    assert "GSM" in text
    assert "GEO" in text
    assert "hover" in text.casefold() or "tooltip" in text.casefold()
    assert "green" in text.casefold()
    assert "orange" in text.casefold()


def test_table_help_lines_include_session_only() -> None:
    lines = table_help_lines()

    assert any("session-only" in line for line in lines)
    assert any("orange" in line.casefold() and "green" in line.casefold() for line in lines)
    assert any("border" in line.casefold() and "both" in line.casefold() for line in lines)
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
