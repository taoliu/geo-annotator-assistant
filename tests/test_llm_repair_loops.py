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
from ingest.read_context_jsonl import iter_gsm_contexts
from ingest.soft_to_context_jsonl import soft_to_context_jsonl
from llm.base import LLMRequest, LLMResult, compute_request_fingerprint
from validator.consistency_validator import ASSAY_PLATFORM_CONFLICT
from validator.ontology_match import OntologyMatch
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
        "tissue_type": "Blood",
        "cell_line": "No",
        "disease": "Healthy",
        "treatment": "None",
    }
    base.update(overrides)
    return json.dumps(base, ensure_ascii=True)


def _load_soft_record(tmp_path: Path, gsm_accession: str) -> dict:
    soft_path = ROOT / "testing_data" / "GSE297202_family.soft.gz"
    jsonl_path = soft_to_context_jsonl(soft_path=str(soft_path), work_dir=tmp_path)
    for record in iter_gsm_contexts(jsonl_path):
        if record["gsm_accession"] == gsm_accession:
            return record
    raise AssertionError(f"Context record not found for {gsm_accession}")


def _matched_ontology(field: str, raw_value: str) -> OntologyMatch:
    return OntologyMatch(
        field=field,
        raw_value=raw_value,
        ontology=f"{field}-test",
        status="MATCHED",
        matched_term_id=f"{field}:1",
        matched_label=raw_value,
        matched_source="test",
        match_type="label_exact",
        score=1.0,
        alternates=[],
    )


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
        "context_text": "Control samples profiled with RNA-seq.",
    }

    outputs = [
        _make_output(
            gse_accession="GSE123456",
            gsm_accession="GSM123456",
            disease="Cancer",
        ),
        _make_output(
            gse_accession="GSE123456",
            gsm_accession="GSM123456",
            disease="Healthy",
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
    assert output["disease"] == "Healthy"
    assert len(audit_record["llm_raw_outputs"]) == 2


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


def test_format_error_details_stage_format_repair(monkeypatch) -> None:
    cfg = _load_stub_config()
    cfg["limits"]["max_format_repairs"] = 1
    cfg["limits"]["field_word_limits"] = {"treatment": 2}
    record = {
        "gsm_accession": "GSM111999",
        "gse_accession": "GSE111999",
        "context_text": "Series Accession: GSE111999\nSample ID: GSM111999\n",
    }

    outputs = [
        _make_output(treatment="too many words here"),
        _make_output(treatment="still too many words"),
    ]
    fake_client = FakeLLMClient(outputs)
    monkeypatch.setattr(
        run_single_module,
        "create_llm_client",
        lambda _cfg: fake_client,
    )

    _, audit_record, flagged = run_single_from_context_record(record, cfg)

    assert flagged is True
    assert ERROR_WORD_LIMIT in audit_record["validation"]["format_errors"]
    assert audit_record["validation"]["format_error_details"] == [
        {
            "code": ERROR_WORD_LIMIT,
            "field": "treatment",
            "limit_used": 2,
            "observed_word_count": 4,
            "stage": "format_repair",
        }
    ]


def test_gsm8986011_noop_terminal_fallback_does_not_spin(
    monkeypatch,
    tmp_path: Path,
) -> None:
    cfg = _load_stub_config()
    record = _load_soft_record(tmp_path, "GSM8986011")

    outputs = [
        _make_output(
            gse_accession="GSE297202",
            gsm_accession="GSM8986011",
            data_type="Microarray",
            organism="Mus musculus",
            tissue_type="Blood",
            cell_line="No",
            disease="Healthy",
            treatment="None",
        ),
        _make_output(
            gse_accession="GSE297202",
            gsm_accession="GSM8986011",
            data_type="Microarray",
            organism="Mus musculus",
            tissue_type="Blood",
            cell_line="No",
            disease="Healthy",
            treatment="None",
        ),
        _make_output(
            gse_accession="GSE297202",
            gsm_accession="GSM8986011",
            data_type="Microarray",
            organism="Mus musculus",
            tissue_type="Blood",
            cell_line="No",
            disease="Healthy",
            treatment="None",
        ),
    ]
    fake_client = FakeLLMClient(outputs)

    def _fake_ground_all_fields(parsed_output, context_text, rag_cfg):
        del context_text, rag_cfg
        matches = {
            field: _matched_ontology(field, parsed_output.get(field, ""))
            for field in ("data_type", "tissue_type", "cell_line", "disease")
        }
        return matches, {}

    monkeypatch.setattr(run_single_module, "ground_all_fields", _fake_ground_all_fields)
    monkeypatch.setattr(
        run_single_module,
        "consistency_validate",
        lambda parsed_output, context_text, **kwargs: [ASSAY_PLATFORM_CONFLICT],
    )

    validation_calls = {"n": 0}

    def _count_validation(_gsm_accession: str) -> None:
        validation_calls["n"] += 1
        if validation_calls["n"] > 6:
            raise AssertionError("validation loop exceeded bounded no-op retries")

    monkeypatch.setattr(
        run_single_module,
        "log_gsm_validation_completed",
        _count_validation,
    )

    output, audit_record, flagged = run_single_from_context_record(
        record,
        cfg,
        llm_client=fake_client,
    )

    assert flagged is False
    assert output["data_type"] == "Unknown"
    assert audit_record["final_decision"] == "ACCEPT"
    assert audit_record["attempts_by_field"] == {"data_type": 3}
    assert audit_record["rationale"]["terminal_fallback_fields"] == ["data_type"]
    assert validation_calls["n"] == 4
