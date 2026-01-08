from __future__ import annotations

import json
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agent.config import load_config
from agent.run_batch import run_batch
from llm.base import LLMRequest, LLMResult, compute_request_fingerprint


def _load_stub_config() -> dict:
    cfg = load_config(str(ROOT / "config" / "example_config.yaml"))
    cfg.setdefault("parser", {})["mode"] = "stub"
    cfg.setdefault("llm", {})["transport"] = "stub"
    cfg.setdefault("rag", {}).setdefault("ontology", {})["enabled"] = False
    return cfg


def _fake_llm_output() -> str:
    return json.dumps(
        {
            "gse_accession": "GSE000000",
            "gsm_accession": "GSM000000",
            "data_type": "RNA-seq",
            "organism": "Homo sapiens",
            "tissue_type": "Blood",
            "cell_line": "No",
            "disease": "Healthy",
            "treatment": "None",
        },
        ensure_ascii=True,
    )


def test_run_batch_initializes_llm_once(monkeypatch) -> None:
    cfg = _load_stub_config()
    calls = {"count": 0}

    class FakeLLMClient:
        def generate(self, request: LLMRequest) -> LLMResult:
            return LLMResult(
                text=_fake_llm_output(),
                request_id=request.request_id,
                usage=None,
                transport_meta={"provider": "fake"},
                request_fingerprint=compute_request_fingerprint(request),
            )

    def _fake_create(_cfg: dict):
        calls["count"] += 1
        return FakeLLMClient()

    import agent.run_batch as run_batch_module

    monkeypatch.setattr(run_batch_module, "create_llm_client", _fake_create)

    run_batch_module.run_batch(["GSM000001", "GSM000002"], cfg)

    assert calls["count"] == 1


def test_run_batch_logs_single_init_for_local_transformers(monkeypatch, capsys) -> None:
    cfg = _load_stub_config()
    cfg["llm"]["transport"] = "local_transformers"
    cfg["llm"]["model_path"] = "fake-model"
    cfg["llm"]["device"] = "cpu"

    class FakeLocalTransformersClient:
        def __init__(self, cfg: dict) -> None:
            self._device = cfg.get("device", "cpu")

        def generate(self, request: LLMRequest) -> LLMResult:
            return LLMResult(
                text=_fake_llm_output(),
                request_id=request.request_id,
                usage=None,
                transport_meta={"provider": "fake_local"},
                request_fingerprint=compute_request_fingerprint(request),
            )

    fake_module = types.SimpleNamespace(
        LocalTransformersClient=FakeLocalTransformersClient
    )
    monkeypatch.setitem(sys.modules, "llm.local_transformers", fake_module)

    run_batch(["GSM000010", "GSM000011"], cfg)

    output = capsys.readouterr().out
    assert output.count("[LLM] Initializing model:") == 1
    assert "[LLM] Reusing existing model instance" in output


def test_run_batch_outputs_are_stable() -> None:
    cfg = _load_stub_config()

    annotations_a, _, flagged_a, summary_a = run_batch(
        ["GSM000020", "GSM000021"], cfg
    )
    annotations_b, _, flagged_b, summary_b = run_batch(
        ["GSM000020", "GSM000021"], cfg
    )

    assert annotations_a == annotations_b
    assert flagged_a == flagged_b
    assert summary_a == summary_b
