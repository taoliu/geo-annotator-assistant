from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ui.gse_navigation import ensure_active_gse, step_active_gse


def test_ensure_active_gse_defaults_to_first_option() -> None:
    assert ensure_active_gse(None, ["GSE1", "GSE2"]) == "GSE1"
    assert ensure_active_gse("UNKNOWN", ["GSE1", "GSE2"]) == "GSE1"


def test_ensure_active_gse_preserves_valid_value() -> None:
    assert ensure_active_gse("GSE2", ["GSE1", "GSE2"]) == "GSE2"


def test_ensure_active_gse_rejects_empty_options() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        ensure_active_gse("GSE1", [])


def test_step_active_gse_prev_and_next_bounds() -> None:
    options = ["GSE1", "GSE2", "GSE3"]

    assert step_active_gse("GSE1", options, "prev") == "GSE1"
    assert step_active_gse("GSE3", options, "next") == "GSE3"
    assert step_active_gse("GSE2", options, "prev") == "GSE1"
    assert step_active_gse("GSE2", options, "next") == "GSE3"


def test_step_active_gse_rejects_invalid_active() -> None:
    with pytest.raises(ValueError, match="not present"):
        step_active_gse("GSE9", ["GSE1", "GSE2"], "next")
