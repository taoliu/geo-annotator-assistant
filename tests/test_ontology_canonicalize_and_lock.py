from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agent.ontology_canonicalization import apply_terminal_exact_canonicalization_and_lock
from agent.repair_loop import apply_repairs
from agent.state import PipelineState
from validator.decision_engine import load_decision_table


def _decision_table() -> dict:
    return load_decision_table(str(ROOT / "spec" / "decision_table.yaml"))


def _config(*, canonicalize: bool = False, lock: bool = False) -> dict:
    return {
        "rag": {
            "ontology": {
                "canonicalize_terminal_exact_labels": canonicalize,
                "lock_terminal_exact_fields": lock,
            }
        }
    }


def _terminal_match() -> dict:
    return {
        "status": "MATCHED",
        "score": 1.0,
        "match_type": "label_norm_exact",
        "matched_label": "Myc-CaP",
        "matched_term_id": "CVCL:J703",
        "matched_source": "Cellosaurus",
    }


def _full_output(*, cell_line: str, disease: str = "Healthy") -> dict:
    return {
        "gse_accession": "GSE000",
        "gsm_accession": "GSM000",
        "data_type": "RNA-Seq",
        "organism": "Homo sapiens",
        "tissue_type": "Heart",
        "cell_line": cell_line,
        "disease": disease,
        "treatment": "None",
    }


def test_canonicalize_terminal_exact_label() -> None:
    state = PipelineState(
        gsm_accession="GSM000",
        final_output={"cell_line": "Myccap"},
        ontology_matches={"cell_line": _terminal_match()},
    )

    apply_terminal_exact_canonicalization_and_lock(
        state,
        _config(canonicalize=True, lock=False),
    )

    assert state.final_output["cell_line"] == "Myc-CaP"
    assert state.canonicalizations["cell_line"]["canonical_value"] == "Myc-CaP"
    assert state.locked_fields == {}


def test_lock_prevents_repair_overwrite() -> None:
    state = PipelineState(
        gsm_accession="GSM001",
        final_output={"cell_line": "Myccap"},
        ontology_matches={"cell_line": _terminal_match()},
        semantic_errors={"cell_line": ["cell_line_inferred_without_evidence"]},
    )
    apply_terminal_exact_canonicalization_and_lock(
        state,
        _config(canonicalize=False, lock=True),
    )

    class DummyLLM:
        def generate(self, request):
            raise AssertionError("Repair should not be scheduled for locked fields.")

    result = apply_repairs(
        state,
        _decision_table(),
        llm_client=DummyLLM(),
        context_text="context",
    )

    assert result.final_output["cell_line"] == "Myc-CaP"
    assert result.attempts_by_field == {}
    assert result.repair_history == []


def test_default_off_regression_allows_repair() -> None:
    state = PipelineState(
        gsm_accession="GSM002",
        final_output={"cell_line": "Myccap"},
        ontology_matches={"cell_line": _terminal_match()},
        semantic_errors={"cell_line": ["cell_line_inferred_without_evidence"]},
    )
    apply_terminal_exact_canonicalization_and_lock(
        state,
        _config(canonicalize=False, lock=False),
    )

    assert state.final_output["cell_line"] == "Myccap"

    class DummyResult:
        def __init__(self, text: str) -> None:
            self.text = text

    class DummyLLM:
        def __init__(self, text: str) -> None:
            self.text = text

        def generate(self, request):
            return DummyResult(self.text)

    repair_output = _full_output(cell_line="FixedLine")
    result = apply_repairs(
        state,
        _decision_table(),
        llm_client=DummyLLM(json.dumps(repair_output)),
        context_text="context",
    )

    assert result.final_output["cell_line"] == "FixedLine"


def test_multi_field_repair_ignores_locked_field() -> None:
    state = PipelineState(
        gsm_accession="GSM003",
        final_output=_full_output(cell_line="Myccap", disease="Healthy"),
        ontology_matches={"cell_line": _terminal_match()},
        semantic_errors={"disease": ["disease_inferred_without_evidence"]},
    )
    apply_terminal_exact_canonicalization_and_lock(
        state,
        _config(canonicalize=True, lock=True),
    )

    class DummyResult:
        def __init__(self, text: str) -> None:
            self.text = text

    class DummyLLM:
        def __init__(self, text: str) -> None:
            self.text = text

        def generate(self, request):
            return DummyResult(self.text)

    repair_output = _full_output(cell_line="ChangedLine", disease="Flu")
    result = apply_repairs(
        state,
        _decision_table(),
        llm_client=DummyLLM(json.dumps(repair_output)),
        context_text="context",
    )

    assert result.final_output["cell_line"] == "Myc-CaP"
    assert result.final_output["disease"] == "Flu"
