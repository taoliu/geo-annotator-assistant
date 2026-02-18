from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agent.repair_loop import apply_repairs
from agent.state import PipelineState
from llm.base import LLMResult
from validator.decision_engine import load_decision_table
from validator.format_validator import ERROR_WORD_LIMIT


def _decision_table() -> dict:
    return load_decision_table(str(ROOT / "spec" / "decision_table.yaml"))


def test_no_failures_accept() -> None:
    state = PipelineState(gsm_accession="GSM000")
    result = apply_repairs(state, _decision_table())
    assert result.final_decision == "ACCEPT"


def test_tissue_repair_then_fallback_unknown() -> None:
    state = PipelineState(
        gsm_accession="GSM111",
        semantic_errors={"tissue_type": ["tissue_type_is_cell_type"]},
    )
    result = apply_repairs(state, _decision_table())
    assert result.final_decision == "ACCEPT"
    assert result.final_output == {"tissue_type": "Unknown"}
    assert result.attempts_by_field["tissue_type"] == 2
    assert len(result.repair_history) == 2
    assert result.repair_history[0]["repair_template"] == "repair_tissue_anatomy_v1"


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


def test_terminal_fallback_blocks_repair() -> None:
    state = PipelineState(
        gsm_accession="GSM556",
        semantic_errors={"cell_line": ["cell_line_is_cell_type"]},
    )
    injected = {"done": False}

    def _reintroduce_failure(current_state: PipelineState) -> None:
        if not injected["done"]:
            current_state.semantic_errors = {}
            current_state.ontology_failures = {
                "cell_line": "ontology_no_match_cell_line"
            }
            injected["done"] = True
        else:
            current_state.semantic_errors = {}
            current_state.ontology_failures = {}

    result = apply_repairs(
        state,
        _decision_table(),
        validation_callback=_reintroduce_failure,
    )
    assert result.final_decision == "ACCEPT"
    assert result.final_output == {"cell_line": "No"}
    assert result.attempts_by_field["cell_line"] == 1
    assert result.terminal_fallback_fields == {"cell_line"}
    assert len(result.repair_history) == 1
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
        semantic_errors={"tissue_type": ["tissue_type_is_cell_type"]},
    )
    result = apply_repairs(state, _decision_table(), max_total_repairs=1)
    assert result.final_decision == "FLAGGED"
    assert "max_repairs_exceeded" in result.flags
    assert result.attempts_by_field["tissue_type"] == 1
    assert len(result.repair_history) == 1


def test_repair_loop_records_format_error_details_for_repair_stage() -> None:
    class _FakeLLM:
        def __init__(self, outputs: list[str]) -> None:
            self._outputs = list(outputs)

        def generate(self, request):
            text = self._outputs.pop(0)
            return LLMResult(
                text=text,
                request_id=request.request_id,
                usage=None,
                transport_meta=None,
                request_fingerprint=None,
            )

    state = PipelineState(
        gsm_accession="GSMRLP",
        gse_accession="GSERLP",
        semantic_errors={"disease": ["disease_inferred_without_evidence"]},
        final_output={"disease": "Unknown"},
    )
    llm = _FakeLLM(
        [
            json.dumps(
                {
                    "gse_accession": "GSERLP",
                    "gsm_accession": "GSMRLP",
                    "data_type": "RNA-seq",
                    "organism": "Homo sapiens",
                    "tissue_type": "blood",
                    "cell_line": "No",
                    "disease": "Healthy",
                    "treatment": "one two three four five six",
                },
                ensure_ascii=True,
            )
        ]
    )

    result = apply_repairs(
        state,
        _decision_table(),
        llm_client=llm,
        context_text="ctx",
        prompt_loader=lambda _name: "repair prompt",
        max_total_repairs=1,
    )

    assert result.final_decision == "FLAGGED"
    assert ERROR_WORD_LIMIT in result.format_errors
    assert result.format_error_details == [
        {
            "code": ERROR_WORD_LIMIT,
            "field": "treatment",
            "limit_used": 5,
            "observed_word_count": 6,
            "stage": "repair_loop",
        }
    ]
