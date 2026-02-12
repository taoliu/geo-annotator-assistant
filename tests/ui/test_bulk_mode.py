from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ui.bulk_mode import (
    activate_bulk_mode,
    is_bulk_mode_active,
    reset_bulk_mode_state,
)


def test_activate_bulk_mode_sets_mode_true() -> None:
    state: dict[str, object] = {"bulk_mode": False}

    activate_bulk_mode(state, "bulk_mode")

    assert state["bulk_mode"] is True
    assert is_bulk_mode_active(state, "bulk_mode") is True


def test_is_bulk_mode_active_coerces_missing_and_truthy_values() -> None:
    state: dict[str, object] = {}
    assert is_bulk_mode_active(state, "bulk_mode") is False
    state["bulk_mode"] = 1
    assert is_bulk_mode_active(state, "bulk_mode") is True


def test_reset_bulk_mode_state_clears_inputs_and_disables_mode() -> None:
    state: dict[str, object] = {
        "bulk_mode": True,
        "bulk_field": "disease",
        "bulk_value": "Healthy",
        "other": "keep",
    }

    reset_bulk_mode_state(
        state,
        mode_key="bulk_mode",
        field_key="bulk_field",
        value_key="bulk_value",
    )

    assert state["bulk_mode"] is False
    assert "bulk_field" not in state
    assert "bulk_value" not in state
    assert state["other"] == "keep"
