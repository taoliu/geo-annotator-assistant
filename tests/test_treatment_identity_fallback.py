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
        "tissue_type": "Blood",
        "cell_line": "No",
        "disease": "Healthy",
        "treatment": "T and NK cell subset",
    }
    base.update(overrides)
    return json.dumps(base, ensure_ascii=True)


def test_treatment_identity_leakage_sets_none_and_flags(monkeypatch) -> None:
    cfg = _load_stub_config()
    record = {
        "gsm_accession": "GSM000222",
        "gse_accession": "GSE000111",
        "context_text": "Blood samples profiled with RNA-seq.",
    }

    outputs = [_make_output(treatment="T and NK cell subset")]
    fake_client = FakeLLMClient(outputs)
    monkeypatch.setattr(
        run_single_module,
        "create_llm_client",
        lambda _cfg: fake_client,
    )

    output, audit_record, flagged = run_single_from_context_record(record, cfg)

    assert flagged is False
    assert audit_record["final_decision"] == "ACCEPT"
    assert output["treatment"] == "None"
    assert "treatment_not_an_intervention" in audit_record["flags"]
    assert audit_record["repair_history"] == []
    assert "repair_template_missing" not in audit_record["flags"]


def test_treatment_real_intervention_unchanged(monkeypatch) -> None:
    cfg = _load_stub_config()
    record = {
        "gsm_accession": "GSM000223",
        "gse_accession": "GSE000111",
        "context_text": "Samples treated with PD-1 blockade.",
    }

    outputs = [_make_output(treatment="PD-1 blockade")]
    fake_client = FakeLLMClient(outputs)
    monkeypatch.setattr(
        run_single_module,
        "create_llm_client",
        lambda _cfg: fake_client,
    )

    output, audit_record, _ = run_single_from_context_record(record, cfg)

    assert output["treatment"] == "PD-1 blockade"
    assert "treatment_not_an_intervention" not in audit_record["flags"]


def test_treatment_genetic_perturbation_descriptor_unchanged(monkeypatch) -> None:
    cfg = _load_stub_config()
    record = {
        "gsm_accession": "GSM5047039",
        "gse_accession": "GSE165621",
        "context_text": "ALDH1B1 KO clone expressing EGFP",
    }

    outputs = [_make_output(treatment="ALDH1B1 KO clone expressing EGFP")]
    fake_client = FakeLLMClient(outputs)
    monkeypatch.setattr(
        run_single_module,
        "create_llm_client",
        lambda _cfg: fake_client,
    )

    output, audit_record, _ = run_single_from_context_record(record, cfg)

    assert output["treatment"] == "ALDH1B1 KO clone expressing EGFP"
    assert "treatment_not_an_intervention" not in audit_record["flags"]
