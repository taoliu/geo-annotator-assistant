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
        "tissue_type": "Tumor",
        "cell_line": "No",
        "disease": "Cancer",
        "treatment": "None",
    }
    base.update(overrides)
    return json.dumps(base, ensure_ascii=True)


def test_tissue_placeholder_sets_unknown_and_flags(monkeypatch) -> None:
    cfg = _load_stub_config()
    record = {
        "gsm_accession": "GSM000222",
        "gse_accession": "GSE000111",
        "context_text": "Tumor samples from lung cancer profiled with RNA-seq.",
    }

    outputs = [_make_output(tissue_type="Tumor")]
    fake_client = FakeLLMClient(outputs)
    monkeypatch.setattr(
        run_single_module,
        "create_llm_client",
        lambda _cfg: fake_client,
    )

    output, audit_record, flagged = run_single_from_context_record(record, cfg)

    assert flagged is True
    assert audit_record["final_decision"] == "FLAGGED"
    assert output["tissue_type"] == "Unknown"
    assert "tissue_type_non_anatomical_placeholder" in audit_record["flags"]
    assert audit_record["repair_history"] == []
    assert audit_record["rationale"]["attempts_by_field"] == {}
    assert audit_record["validation"]["ontology_matches"]["tissue_type"]["matched_via"] == (
        "non_anatomical_placeholder"
    )
    assert audit_record["llm_parsed_outputs"][0]["tissue_type"] == "Tumor"


def test_tissue_placeholder_does_not_affect_anatomical_value(monkeypatch) -> None:
    cfg = _load_stub_config()
    record = {
        "gsm_accession": "GSM000223",
        "gse_accession": "GSE000111",
        "context_text": "Lung samples profiled with RNA-seq.",
    }

    outputs = [_make_output(tissue_type="Lung", disease="Healthy")]
    fake_client = FakeLLMClient(outputs)
    monkeypatch.setattr(
        run_single_module,
        "create_llm_client",
        lambda _cfg: fake_client,
    )

    output, audit_record, flagged = run_single_from_context_record(record, cfg)

    assert output["tissue_type"] == "Lung"
    assert "tissue_type_non_anatomical_placeholder" not in audit_record["flags"]
