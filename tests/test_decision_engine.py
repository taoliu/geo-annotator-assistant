from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from validator.decision_engine import decide_next_action


def _decision_table() -> dict:
    return {
        "tissue_type_is_cell_type": {
            "action": "REPAIR",
            "field": "tissue_type",
            "repair_template": "repair_tissue_anatomy_v1",
            "max_attempts": 1,
            "fallback_value": "Unknown",
            "severity": "medium",
        },
        "disease_unsupported": {
            "action": "FALLBACK",
            "field": "disease",
            "repair_template": None,
            "max_attempts": 0,
            "fallback_value": "Healthy",
            "severity": "medium",
        },
    }


def test_empty_failures_accept() -> None:
    decision = decide_next_action({}, {}, _decision_table())
    assert decision.decision_type == "ACCEPT"
    assert decision.field is None
    assert decision.failure_code is None


def test_tissue_repair_before_max_attempts() -> None:
    failures = {"tissue_type": ["tissue_type_is_cell_type"]}
    attempts = {"tissue_type": 0}
    decision = decide_next_action(failures, attempts, _decision_table())
    assert decision.decision_type == "REPAIR"
    assert decision.field == "tissue_type"
    assert decision.failure_code == "tissue_type_is_cell_type"
    assert decision.repair_template == "repair_tissue_anatomy_v1"


def test_tissue_fallback_after_max_attempts() -> None:
    failures = {"tissue_type": ["tissue_type_is_cell_type"]}
    attempts = {"tissue_type": 1}
    decision = decide_next_action(failures, attempts, _decision_table())
    assert decision.decision_type == "FALLBACK"
    assert decision.field == "tissue_type"
    assert decision.fallback_value == "Unknown"


def test_disease_unsupported_fallback() -> None:
    failures = {"disease": ["disease_unsupported"]}
    decision = decide_next_action(failures, {}, _decision_table())
    assert decision.decision_type == "FALLBACK"
    assert decision.field == "disease"
    assert decision.fallback_value == "Healthy"


def test_unknown_failure_code_escalates() -> None:
    failures = {"data_type": ["unknown_failure"]}
    decision = decide_next_action(failures, {}, _decision_table())
    assert decision.decision_type == "ESCALATE"
    assert decision.failure_code == "unknown_failure"
    assert decision.severity == "high"
