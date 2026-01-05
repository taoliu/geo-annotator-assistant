from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agent.repair_loop import apply_repairs
from agent.state import PipelineState
from validator.decision_engine import load_decision_table


def _decision_table() -> dict:
    return load_decision_table(str(ROOT / "spec" / "decision_table.yaml"))


def test_no_failures_accept() -> None:
    state = PipelineState(gsm_accession="GSM000")
    result = apply_repairs(state, _decision_table())
    assert result.final_decision == "ACCEPT"


def test_tissue_repair_then_fallback_unknown() -> None:
    state = PipelineState(
        gsm_accession="GSM111",
        semantic_errors={"tissue_type": ["tissue_is_cell_type"]},
    )
    result = apply_repairs(state, _decision_table())
    assert result.final_decision == "ACCEPT"
    assert result.final_output == {"tissue_type": "Unknown"}
    assert result.attempts_by_field["tissue_type"] == 3
    assert len(result.repair_history) == 3
    assert result.repair_history[0]["repair_template"] == "repair_tissue_v1"
    assert result.repair_history[1]["repair_template"] == "repair_tissue_v1"


def test_disease_unsupported_fallback_healthy() -> None:
    state = PipelineState(
        gsm_accession="GSM222",
        semantic_errors={"disease": ["disease_unsupported"]},
    )
    result = apply_repairs(state, _decision_table())
    assert result.final_decision == "ACCEPT"
    assert result.final_output == {"disease": "Healthy"}
    assert result.attempts_by_field["disease"] == 1
    assert len(result.repair_history) == 1
    assert result.repair_history[0]["failure_code"] == "disease_unsupported"


def test_cell_line_is_cell_type_fallback_no() -> None:
    state = PipelineState(
        gsm_accession="GSM555",
        semantic_errors={"cell_line": ["cell_line_is_cell_type"]},
    )
    result = apply_repairs(state, _decision_table())
    assert result.final_decision == "ACCEPT"
    assert result.final_output == {"cell_line": "No"}
    assert result.attempts_by_field["cell_line"] == 1
    assert result.repair_history[0]["failure_code"] == "cell_line_is_cell_type"


def test_unknown_failure_escalates() -> None:
    state = PipelineState(
        gsm_accession="GSM333",
        semantic_errors={"data_type": ["unknown_failure"]},
    )
    result = apply_repairs(state, _decision_table())
    assert result.final_decision == "FLAGGED"
    assert "unknown_failure" in result.flags
    assert result.attempts_by_field == {}
    assert result.repair_history == []


def test_max_total_repairs_enforced() -> None:
    state = PipelineState(
        gsm_accession="GSM444",
        semantic_errors={"tissue_type": ["tissue_is_cell_type"]},
    )
    result = apply_repairs(state, _decision_table(), max_total_repairs=1)
    assert result.final_decision == "FLAGGED"
    assert "max_repairs_exceeded" in result.flags
    assert result.attempts_by_field["tissue_type"] == 1
    assert len(result.repair_history) == 1
