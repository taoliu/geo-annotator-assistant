from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agent.config import load_config
from agent.run_single import run_single_from_context_record
import agent.run_single as run_single_module
from llm.base import LLMRequest, LLMResult, compute_request_fingerprint


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
        "disease": "CT26 mouse tumor model",
        "treatment": "None",
    }
    base.update(overrides)
    return json.dumps(base, ensure_ascii=True)


def test_disease_model_identifier_falls_back_and_flags(monkeypatch) -> None:
    cfg = _load_stub_config()
    record = {
        "gsm_accession": "GSM000222",
        "gse_accession": "GSE000111",
        "context_text": "Mouse tumor model samples profiled with RNA-seq.",
    }

    outputs = [_make_output(disease="CT26 mouse tumor model")]
    fake_client = FakeLLMClient(outputs)
    monkeypatch.setattr(
        run_single_module,
        "create_llm_client",
        lambda _cfg: fake_client,
    )

    output, audit_record, flagged = run_single_from_context_record(record, cfg)

    assert flagged is True
    assert audit_record["final_decision"] == "FLAGGED"
    assert output["disease"] == "Unknown"
    assert "disease_model_identifier_not_ontology" in audit_record["flags"]
    assert audit_record["repair_history"] == []
    assert audit_record["rationale"]["attempts_by_field"] == {}
    assert audit_record["validation"]["ontology_matches"]["disease"]["matched_via"] == (
        "model_identifier"
    )
    assert audit_record["llm_parsed_outputs"][0]["disease"] == "CT26 mouse tumor model"


def test_disease_model_identifier_does_not_apply_with_disease_term(monkeypatch) -> None:
    cfg = _load_stub_config()
    record = {
        "gsm_accession": "GSM000223",
        "gse_accession": "GSE000111",
        "context_text": "Melanoma cancer samples profiled with RNA-seq.",
    }

    outputs = [_make_output(disease="B16 melanoma model")]
    fake_client = FakeLLMClient(outputs)
    monkeypatch.setattr(
        run_single_module,
        "create_llm_client",
        lambda _cfg: fake_client,
    )

    output, audit_record, flagged = run_single_from_context_record(record, cfg)

    assert output["disease"] == "B16 melanoma model"
    assert "disease_model_identifier_not_ontology" not in audit_record["flags"]
    assert audit_record["validation"]["ontology_matches"]["disease"]["matched_via"] != (
        "model_identifier"
    )
