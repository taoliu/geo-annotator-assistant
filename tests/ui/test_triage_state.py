from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ui.triage_state import merge_options_with_selected, normalize_triage_state


def test_normalize_triage_state_defaults_when_missing() -> None:
    normalized = normalize_triage_state(
        None,
        decision_options=("All", "FLAGGED", "ACCEPT"),
        sort_options=("Default", "Decision"),
    )
    assert normalized == {
        "decision": "All",
        "primary": [],
        "flags": [],
        "sort_by": "Default",
        "sort_desc": True,
    }


def test_normalize_triage_state_validates_and_deduplicates() -> None:
    normalized = normalize_triage_state(
        {
            "decision": "FLAGGED",
            "primary": ["a", "a", "", 1, "b"],
            "flags": ["x", "x", "y"],
            "sort_by": "Decision",
            "sort_desc": False,
        },
        decision_options=("All", "FLAGGED", "ACCEPT"),
        sort_options=("Default", "Decision"),
    )
    assert normalized == {
        "decision": "FLAGGED",
        "primary": ["a", "b"],
        "flags": ["x", "y"],
        "sort_by": "Decision",
        "sort_desc": False,
    }


def test_merge_options_with_selected_keeps_selected_values() -> None:
    merged = merge_options_with_selected(["one", "two"], ["two", "three", ""])
    assert merged == ["one", "two", "three"]
