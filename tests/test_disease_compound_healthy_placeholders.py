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

    def generate(self, request: LLMRequest) -> LLMResult:
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
    return cfg


def _make_output(**overrides: str) -> str:
    base = {
        "gse_accession": "GSE000111",
        "gsm_accession": "GSM000444",
        "data_type": "RNA-seq",
        "organism": "Homo sapiens",
        "tissue_type": "blood",
        "cell_line": "No",
        "disease": "NA (Healthy Donors)",
        "treatment": "None",
    }
    base.update(overrides)
    return json.dumps(base, ensure_ascii=True)


def test_pipeline_normalizes_compound_healthy_placeholder_without_repair(monkeypatch) -> None:
    cfg = _load_stub_config()
    record = {
        "gsm_accession": "GSM000444",
        "gse_accession": "GSE000111",
        "context_text": (
            "Series Accession: GSE000111\n"
            "Sample ID: GSM000444\n"
            "Sample Organism: Homo sapiens\n"
            "Sample Title: healthy donor blood sample\n"
        ),
    }

    outputs = [_make_output(disease="NA (Healthy Donors)")]
    fake_client = FakeLLMClient(outputs)
    monkeypatch.setattr(run_single_module, "create_llm_client", lambda _cfg: fake_client)

    output, audit_record, flagged = run_single_from_context_record(record, cfg)

    assert flagged is False
    assert audit_record["final_decision"] == "ACCEPT"
    assert output["disease"] == "Healthy"
    assert audit_record["attempts_by_field"].get("disease", 0) == 0
    assert "ontology_low_confidence_disease" not in audit_record["flags"]
    assert audit_record["validation"]["ontology_matches"]["disease"]["matched_via"] == (
        "healthy_control_normalized"
    )
