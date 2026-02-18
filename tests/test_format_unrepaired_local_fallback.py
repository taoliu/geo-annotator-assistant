from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agent.config import load_config
from agent.run_single import (
    _finalize_unrepaired_format_errors,
    run_single_from_context_record,
)
from agent.state import PipelineState
import agent.run_single as run_single_module
from llm.base import LLMRequest, LLMResult, compute_request_fingerprint
from validator.format_validator import ERROR_WORD_LIMIT


class FakeLLMClient:
    def __init__(self, outputs: list[str]) -> None:
        self._outputs = list(outputs)
        self.prompts: list[str] = []

    def generate(self, request: LLMRequest) -> LLMResult:
        self.prompts.append(request.prompt)
        if not self._outputs:
            raise AssertionError("FakeLLMClient has no remaining outputs.")
        text = self._outputs.pop(0)
        return LLMResult(
            text=text,
            request_id=request.request_id,
            usage=None,
            transport_meta={"provider": "fake"},
            request_fingerprint=compute_request_fingerprint(request),
        )


def _load_stub_config() -> dict:
    cfg = load_config(str(ROOT / "config" / "example_config.yaml"))
    cfg.setdefault("llm", {})["transport"] = "stub"
    cfg.setdefault("limits", {})
    return cfg


def _make_output(**overrides: str) -> str:
    base = {
        "gse_accession": "GSE000111",
        "gsm_accession": "GSM000222",
        "data_type": "RNA-seq",
        "organism": "Homo sapiens",
        "tissue_type": "Lung",
        "cell_line": "No",
        "disease": "Influenza",
        "treatment": "None",
    }
    base.update(overrides)
    return json.dumps(base, ensure_ascii=True)


def test_unrepaired_format_error_is_field_local(monkeypatch) -> None:
    cfg = _load_stub_config()
    cfg["limits"]["max_format_repairs"] = 0
    cfg["limits"]["field_word_limits"] = {"treatment": 2}
    record = {
        "gsm_accession": "GSM000222",
        "gse_accession": "GSE000111",
        "context_text": "Lung influenza samples profiled with RNA-seq.",
    }

    outputs = [_make_output(treatment="very long treatment string")]
    fake_client = FakeLLMClient(outputs)
    monkeypatch.setattr(
        run_single_module,
        "create_llm_client",
        lambda _cfg: fake_client,
    )

    output, audit_record, flagged = run_single_from_context_record(record, cfg)

    assert flagged is True
    assert audit_record["final_decision"] == "FLAGGED"
    assert "format_unrepaired" in audit_record["flags"]
    assert output["data_type"] == "RNA-seq"
    assert output["organism"] == "Homo sapiens"
    assert output["tissue_type"] == "Lung"
    assert output["disease"] == "Influenza"
    assert output["treatment"] == "None"
    assert ERROR_WORD_LIMIT in audit_record["validation"]["format_errors"]
    assert audit_record["validation"]["format_error_details"] == [
        {
            "code": ERROR_WORD_LIMIT,
            "field": "treatment",
            "limit_used": 2,
            "observed_word_count": 4,
            "stage": "initial",
        }
    ]


def test_locked_field_survives_unrepaired_format_error() -> None:
    cfg = {
        "limits": {"field_word_limits": {"data_type": 1}},
        "rag": {},
    }
    state = PipelineState(
        gsm_accession="GSMLOCK",
        gse_accession="GSELOCK",
    )
    state.locked_fields = {
        "data_type": {
            "label": "RNA-seq data",
            "source": "EFO",
            "reason": "ontology_terminal_exact",
        }
    }
    state.format_errors = [ERROR_WORD_LIMIT]

    parsed_output = {
        "gse_accession": "GSELOCK",
        "gsm_accession": "GSMLOCK",
        "data_type": "RNA-seq data",
        "organism": "Homo sapiens",
        "tissue_type": "Lung",
        "cell_line": "No",
        "disease": "Healthy",
        "treatment": "None",
    }

    _finalize_unrepaired_format_errors(state, parsed_output, "", cfg)

    assert state.final_output is not None
    assert state.final_output["data_type"] == "RNA-seq data"
    assert state.final_decision == "FLAGGED"
    assert "format_unrepaired" in state.flags


def test_spaced_accessions_do_not_trigger_word_limit_after_pre_validation_override(
    monkeypatch,
) -> None:
    cfg = _load_stub_config()
    cfg["limits"]["max_format_repairs"] = 0
    cfg["limits"]["field_word_limits"] = {
        "tissue_type": 10,
        "disease": 10,
        "treatment": 0,
    }
    record = {
        "gsm_accession": "GSM7091755",
        "gse_accession": "GSE227108",
        "context_text": "Lung influenza samples profiled with RNA-seq.",
    }
    outputs = [
        _make_output(
            gse_accession="GSE2 7 1 0 8 9",
            gsm_accession="GSM7 0 9 1 7 5 6",
        )
    ]
    fake_client = FakeLLMClient(outputs)
    def _no_failures(state, _parsed_output, _context_text, _cfg):
        state.semantic_errors = {}
        state.ontology_failures = {}
        state.consistency_flags = []
    monkeypatch.setattr(
        run_single_module,
        "_update_validation_state",
        _no_failures,
    )
    monkeypatch.setattr(
        run_single_module,
        "create_llm_client",
        lambda _cfg: fake_client,
    )

    _, audit_record, flagged = run_single_from_context_record(record, cfg)

    assert flagged is False
    assert audit_record["validation"]["format_errors"] == []
    assert audit_record["validation"]["format_error_details"] == []
    assert "format_unrepaired" not in audit_record["flags"]
    assert len(audit_record["llm_raw_outputs"]) == 1
    assert audit_record["llm_parsed_outputs"][0]["gse_accession"] == "GSE227108"
    assert audit_record["llm_parsed_outputs"][0]["gsm_accession"] == "GSM7091755"
    assert audit_record["final_output"]["gse_accession"] == "GSE227108"
    assert audit_record["final_output"]["gsm_accession"] == "GSM7091755"


def test_non_accession_word_limit_still_triggers(monkeypatch) -> None:
    cfg = _load_stub_config()
    cfg["limits"]["max_format_repairs"] = 0
    cfg["limits"]["field_word_limits"] = {"disease": 2, "treatment": 0}
    record = {
        "gsm_accession": "GSM001122",
        "gse_accession": "GSE001122",
        "context_text": "Validation context text.",
    }
    outputs = [_make_output(disease="very long disease label")]
    fake_client = FakeLLMClient(outputs)
    monkeypatch.setattr(
        run_single_module,
        "create_llm_client",
        lambda _cfg: fake_client,
    )

    _, audit_record, flagged = run_single_from_context_record(record, cfg)

    assert flagged is True
    assert audit_record["validation"]["format_errors"] == [ERROR_WORD_LIMIT]
    assert "format_unrepaired" in audit_record["flags"]
    assert audit_record["validation"]["format_error_details"] == [
        {
            "code": ERROR_WORD_LIMIT,
            "field": "disease",
            "limit_used": 2,
            "observed_word_count": 4,
            "stage": "initial",
        }
    ]
