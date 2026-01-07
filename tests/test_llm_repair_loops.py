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


class FakeLLMClient:
    def __init__(self, outputs: list[str]) -> None:
        self._outputs = list(outputs)
        self.prompts: list[str] = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        if not self._outputs:
            raise AssertionError("FakeLLMClient has no remaining outputs.")
        return self._outputs.pop(0)


def _load_stub_config() -> dict:
    cfg = load_config(str(ROOT / "config" / "example_config.yaml"))
    cfg.setdefault("llm", {})["mode"] = "stub"
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
        "treatment": "None",
    }
    base.update(overrides)
    return json.dumps(base, ensure_ascii=True)


def test_format_repair_pre_loop_fixes_word_limit(monkeypatch) -> None:
    cfg = _load_stub_config()
    cfg.setdefault("limits", {})["field_word_limits"] = {"treatment": 5}
    record = {
        "gsm_accession": "GSM000222",
        "gse_accession": "GSE000111",
        "context_text": "Control blood samples profiled with RNA-seq.",
    }

    outputs = [
        _make_output(treatment="very long treatment string goes here"),
        _make_output(treatment="None"),
    ]
    fake_client = FakeLLMClient(outputs)
    monkeypatch.setattr(
        run_single_module,
        "create_llm_client",
        lambda _cfg: fake_client,
    )

    _, audit_record, flagged = run_single_from_context_record(record, cfg)

    assert flagged is False
    assert audit_record["final_decision"] == "ACCEPT"
    assert len(audit_record["llm_raw_outputs"]) == 2
    assert audit_record["validation"]["format_errors"] == []


def test_accession_override_from_context_record(monkeypatch) -> None:
    cfg = _load_stub_config()
    record = {
        "gsm_accession": "GSM1791882",
        "gse_accession": "GSE229352",
        "context_text": "Series Accession: GSE229352\nSample ID: GSM1791882\n",
    }

    outputs = [
        _make_output(
            gse_accession="GSE2-9-2352",
            gsm_accession="GSM1-7-9182",
        )
    ]
    fake_client = FakeLLMClient(outputs)
    monkeypatch.setattr(
        run_single_module,
        "create_llm_client",
        lambda _cfg: fake_client,
    )

    output, audit_record, flagged = run_single_from_context_record(record, cfg)

    assert flagged is False
    assert output["gse_accession"] == "GSE229352"
    assert output["gsm_accession"] == "GSM1791882"
    assert audit_record["final_output"]["gse_accession"] == "GSE229352"
    assert audit_record["final_output"]["gsm_accession"] == "GSM1791882"


def test_decision_repair_updates_disease(monkeypatch) -> None:
    cfg = _load_stub_config()
    record = {
        "gsm_accession": "GSM123456",
        "gse_accession": "GSE123456",
        "context_text": "Cancer samples were profiled using RNA-seq.",
    }

    outputs = [
        _make_output(gse_accession="GSE123456", gsm_accession="GSM123456"),
        _make_output(
            gse_accession="GSE123456",
            gsm_accession="GSM123456",
            disease="Cancer",
        ),
    ]
    fake_client = FakeLLMClient(outputs)
    monkeypatch.setattr(
        run_single_module,
        "create_llm_client",
        lambda _cfg: fake_client,
    )

    output, audit_record, flagged = run_single_from_context_record(record, cfg)

    assert flagged is False
    assert audit_record["final_decision"] == "ACCEPT"
    assert output["disease"] == "Cancer"


def test_unrepaired_format_flags(monkeypatch) -> None:
    cfg = _load_stub_config()
    cfg["limits"]["max_format_repairs"] = 1
    record = {
        "gsm_accession": "GSM999999",
        "gse_accession": "GSE999999",
        "context_text": "Series Accession: GSE999999\nSample ID: GSM999999\n",
    }

    outputs = ["{invalid json", "{still invalid"]
    fake_client = FakeLLMClient(outputs)
    monkeypatch.setattr(
        run_single_module,
        "create_llm_client",
        lambda _cfg: fake_client,
    )

    _, audit_record, flagged = run_single_from_context_record(record, cfg)

    assert flagged is True
    assert audit_record["final_decision"] == "FLAGGED"
    assert "format_unrepaired" in audit_record["flags"]
