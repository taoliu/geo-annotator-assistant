from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ui.help_text import gsm_accession_tooltip, table_guidance_text, table_help_lines


def test_table_guidance_text_mentions_accession() -> None:
    text = table_guidance_text()

    assert "GSM accession" in text
    assert "open details" in text.casefold()


def test_table_help_lines_include_session_only() -> None:
    lines = table_help_lines()

    assert any("session-only" in line for line in lines)
    assert any("close" in line.casefold() for line in lines)
    assert gsm_accession_tooltip() == "Open details"
