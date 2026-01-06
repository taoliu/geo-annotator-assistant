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
from validator.format_validator import ERROR_INVALID_JSON, validate_format


class FakeLLMClient:
    def __init__(self, outputs: list[str]) -> None:
        self._outputs = list(outputs)
        self.prompts: list[str] = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        if not self._outputs:
            raise AssertionError("FakeLLMClient has no remaining outputs.")
        return self._outputs.pop(0)


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


def test_validator_extracts_fenced_json() -> None:
    raw = (
        "Here is JSON:\n```json\n"
        + _make_output(gse_accession="GSE1", gsm_accession="GSM1")
        + "\n```\nSome text"
    )
    parsed, errors = validate_format(
        raw,
        [
            "gse_accession",
            "gsm_accession",
            "data_type",
            "organism",
            "tissue_type",
            "cell_line",
            "disease",
            "treatment",
        ],
    )
    assert parsed is not None
    assert ERROR_INVALID_JSON not in errors


def test_validator_extracts_balanced_object() -> None:
    raw = 'prefix {"a": "ok"} suffix'
    parsed, errors = validate_format(raw, ["a"])
    assert parsed == {"a": "ok"}
    assert ERROR_INVALID_JSON not in errors


def test_run_single_accepts_long_treatment_without_repair(monkeypatch) -> None:
    cfg = load_config(str(ROOT / "config" / "example_config.yaml"))
    cfg.setdefault("llm", {})["mode"] = "stub"
    cfg.setdefault("limits", {})["max_format_repairs"] = 2

    record = {
        "gsm_accession": "GSM000222",
        "gse_accession": "GSE000111",
        "context_text": "Control blood samples profiled with RNA-seq.",
    }

    outputs = [
        _make_output(treatment="very long treatment string goes here"),
        "```json\n"
        + _make_output(treatment="None")
        + "\n```\nExtra commentary",
        "not used",
    ]
    fake_client = FakeLLMClient(outputs)
    monkeypatch.setattr(
        run_single_module,
        "create_llm_client",
        lambda _cfg: fake_client,
    )

    _, audit_record, flagged = run_single_from_context_record(record, cfg)

    assert flagged is False
    assert audit_record["validation"]["format_errors"] == []
    assert len(audit_record["llm_raw_outputs"]) == 1
