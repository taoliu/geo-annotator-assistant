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
from validator.failure_codes import (
    CELL_LINE_INFERRED_WITHOUT_EVIDENCE,
    CELL_LINE_IS_CELL_TYPE,
    DISEASE_INFERRED_WITHOUT_EVIDENCE,
    TISSUE_TYPE_IS_CELL_TYPE,
)


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
    cfg.setdefault("rag", {}).setdefault("ontology", {})["enabled"] = False
    return cfg


def _make_output(**overrides: str) -> str:
    base = {
        "gse_accession": "GSE000111",
        "gsm_accession": "GSM000222",
        "data_type": "RNA-seq",
        "organism": "Homo sapiens",
        "tissue_type": "Liver",
        "cell_line": "No",
        "disease": "Healthy",
        "treatment": "None",
    }
    base.update(overrides)
    return json.dumps(base, ensure_ascii=True)


def test_disease_inferred_without_evidence_repairs(monkeypatch) -> None:
    cfg = _load_stub_config()
    record = {
        "gsm_accession": "GSM000222",
        "gse_accession": "GSE000111",
        "context_text": "Primary liver tissue profiled with RNA-seq.",
    }

    outputs = [
        _make_output(disease="Hepatocellular carcinoma"),
        _make_output(disease="Healthy"),
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
    assert output["disease"] == "Healthy"
    assert audit_record["attempts_by_field"]["disease"] == 1
    assert audit_record["repair_history"][0]["failure_code"] == (
        DISEASE_INFERRED_WITHOUT_EVIDENCE
    )


def test_cell_line_inferred_without_evidence_repairs(monkeypatch) -> None:
    cfg = _load_stub_config()
    record = {
        "gsm_accession": "GSM000333",
        "gse_accession": "GSE000333",
        "context_text": "Primary hepatocyte samples profiled with RNA-seq.",
    }

    outputs = [
        _make_output(cell_line="HepG2"),
        _make_output(cell_line="No"),
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
    assert output["cell_line"] == "No"
    assert audit_record["attempts_by_field"]["cell_line"] == 1
    assert audit_record["repair_history"][0]["failure_code"] == (
        CELL_LINE_INFERRED_WITHOUT_EVIDENCE
    )


def test_inferred_without_evidence_escalates_after_repair(monkeypatch) -> None:
    cfg = _load_stub_config()
    record = {
        "gsm_accession": "GSM000444",
        "gse_accession": "GSE000444",
        "context_text": "Primary breast tissue profiled with RNA-seq.",
    }

    outputs = [
        _make_output(disease="Breast cancer"),
        _make_output(disease="Breast cancer"),
    ]
    fake_client = FakeLLMClient(outputs)
    monkeypatch.setattr(
        run_single_module,
        "create_llm_client",
        lambda _cfg: fake_client,
    )

    _, audit_record, flagged = run_single_from_context_record(record, cfg)

    assert flagged is True
    assert audit_record["final_decision"] == "FLAGGED"
    assert DISEASE_INFERRED_WITHOUT_EVIDENCE in audit_record["flags"]
    assert audit_record["attempts_by_field"]["disease"] == 1


def test_cell_line_cell_type_fallback(monkeypatch) -> None:
    cfg = _load_stub_config()
    record = {
        "gsm_accession": "GSM000555",
        "gse_accession": "GSE000555",
        "context_text": "PBMC samples were profiled with RNA-seq.",
    }

    outputs = [
        _make_output(cell_line="CD8+ T cells"),
    ]
    fake_client = FakeLLMClient(outputs)
    monkeypatch.setattr(
        run_single_module,
        "create_llm_client",
        lambda _cfg: fake_client,
    )
    monkeypatch.setattr(
        run_single_module,
        "ground_all_fields",
        lambda *_args, **_kwargs: ({}, {}),
    )

    output, audit_record, flagged = run_single_from_context_record(record, cfg)

    assert flagged is False
    assert audit_record["final_decision"] == "ACCEPT"
    assert output["cell_line"] == "No"
    assert audit_record["attempts_by_field"]["cell_line"] == 1
    assert audit_record["repair_history"][0]["failure_code"] == CELL_LINE_IS_CELL_TYPE


def test_tissue_type_cell_type_repairs_to_anatomy(monkeypatch) -> None:
    cfg = _load_stub_config()
    record = {
        "gsm_accession": "GSM7159182",
        "gse_accession": "GSE229352",
        "context_text": (
            "Sample Source Name: Primary mouse mammary fibroblasts line\n"
            "Series Summary: Senescent mouse mammary fibroblasts were harvested."
        ),
    }

    outputs = [
        _make_output(tissue_type="Primary mouse mammary fibroblasts"),
        _make_output(tissue_type="Breast"),
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
    assert output["tissue_type"] in {"Breast", "Unknown"}
    assert audit_record["attempts_by_field"]["tissue_type"] == 1
    assert audit_record["repair_history"][0]["failure_code"] == TISSUE_TYPE_IS_CELL_TYPE


def test_audit_records_repair_attempt(monkeypatch) -> None:
    cfg = _load_stub_config()
    record = {
        "gsm_accession": "GSM000555",
        "gse_accession": "GSE000555",
        "context_text": "Liver tissue profiled with RNA-seq.",
    }

    outputs = [
        _make_output(disease="Cholangiocarcinoma"),
        _make_output(disease="Healthy"),
    ]
    fake_client = FakeLLMClient(outputs)
    monkeypatch.setattr(
        run_single_module,
        "create_llm_client",
        lambda _cfg: fake_client,
    )

    _, audit_record, flagged = run_single_from_context_record(record, cfg)

    assert flagged is False
    assert audit_record["repair_history"]
    repair_entry = audit_record["repair_history"][0]
    assert repair_entry["field"] == "disease"
    assert repair_entry["failure_code"] == DISEASE_INFERRED_WITHOUT_EVIDENCE
    assert repair_entry["repair_template"] == "repair_disease_evidence_v1"
    assert audit_record["attempts_by_field"] == {"disease": 1}
