from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agent.config import load_config
from agent.run_gse import run_gse_from_jsonl
from llm.base import LLMRequest, LLMResult, compute_request_fingerprint


def _load_stub_config() -> dict:
    cfg = load_config(str(ROOT / "config" / "example_config.yaml"))
    cfg.setdefault("llm", {})["transport"] = "stub"
    cfg.setdefault("rag", {}).setdefault("ontology", {})["enabled"] = False
    cfg["llm_cache"] = {"enabled": True}
    return cfg


def _write_jsonl(path: Path, records: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record))
            handle.write("\n")


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


class _CountingClient:
    def __init__(self) -> None:
        self.calls = 0

    def generate(self, request: LLMRequest) -> LLMResult:
        self.calls += 1
        return LLMResult(
            text=_fake_llm_output(),
            request_id=request.request_id,
            usage=None,
            transport_meta={"provider": "counting"},
            request_fingerprint=compute_request_fingerprint(request),
        )


def test_llm_cache_reuses_within_gse(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    cfg = _load_stub_config()
    records = [
        {
            "context_text": (
                "Series Accession: GSE123\n"
                "Sample ID: GSM001\n"
                "Sample Title: patient_01\n"
                "Sample Characteristics: disease=healthy\n"
            ),
            "gsm_accession": "GSM001",
            "gse_accession": "GSE123",
        },
        {
            "context_text": (
                "Series Accession: GSE123\n"
                "Sample ID: GSM002\n"
                "Sample Title: patient_02\n"
                "Sample Characteristics: disease=healthy\n"
            ),
            "gsm_accession": "GSM002",
            "gse_accession": "GSE123",
        },
    ]
    jsonl_path = tmp_path / "contexts.jsonl"
    _write_jsonl(jsonl_path, records)

    client = _CountingClient()
    import agent.run_gse as run_gse_module

    monkeypatch.setattr(run_gse_module, "create_llm_client", lambda _cfg: client)

    _, audits, _, _, _, _ = run_gse_from_jsonl(str(jsonl_path), cfg)

    assert client.calls == 1
    assert audits[0]["llm_cache_hits"] == [False]
    assert audits[1]["llm_cache_hits"] == [True]
    assert audits[0]["llm_cache_stats"]["hits"] == 1
    assert audits[0]["llm_cache_stats"]["misses"] == 1


def test_llm_cache_isolated_by_gse(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    cfg = _load_stub_config()
    records = [
        {
            "context_text": (
                "Series Accession: GSE111\n"
                "Sample ID: GSM010\n"
                "Sample Title: patient_01\n"
                "Sample Characteristics: disease=healthy\n"
            ),
            "gsm_accession": "GSM010",
            "gse_accession": "GSE111",
        },
        {
            "context_text": (
                "Series Accession: GSE222\n"
                "Sample ID: GSM020\n"
                "Sample Title: patient_02\n"
                "Sample Characteristics: disease=healthy\n"
            ),
            "gsm_accession": "GSM020",
            "gse_accession": "GSE222",
        },
    ]
    jsonl_path = tmp_path / "contexts.jsonl"
    _write_jsonl(jsonl_path, records)

    client = _CountingClient()
    import agent.run_gse as run_gse_module

    monkeypatch.setattr(run_gse_module, "create_llm_client", lambda _cfg: client)

    _, audits, _, _, _, _ = run_gse_from_jsonl(str(jsonl_path), cfg)

    assert client.calls == 2
    assert audits[0]["llm_cache_hits"] == [False]
    assert audits[1]["llm_cache_hits"] == [False]


def test_validation_skipped_on_cache_hit(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    cfg = _load_stub_config()
    records = [
        {
            "context_text": (
                "Series Accession: GSE333\n"
                "Sample ID: GSM030\n"
                "Sample Title: patient_01\n"
                "Sample Characteristics: disease=healthy\n"
            ),
            "gsm_accession": "GSM030",
            "gse_accession": "GSE333",
        },
        {
            "context_text": (
                "Series Accession: GSE333\n"
                "Sample ID: GSM031\n"
                "Sample Title: patient_02\n"
                "Sample Characteristics: disease=healthy\n"
            ),
            "gsm_accession": "GSM031",
            "gse_accession": "GSE333",
        },
    ]
    jsonl_path = tmp_path / "contexts.jsonl"
    _write_jsonl(jsonl_path, records)

    calls = {"semantic": 0, "consistency": 0, "ground": 0}

    import agent.run_single as run_single_module

    def _fake_semantic(parsed_output, context_text):
        calls["semantic"] += 1
        return {}

    def _fake_consistency(parsed_output, context_text):
        calls["consistency"] += 1
        return []

    def _fake_ground(parsed_output, context_text, rag_cfg):
        calls["ground"] += 1
        return {}, {}

    monkeypatch.setattr(run_single_module, "semantic_validate", _fake_semantic)
    monkeypatch.setattr(run_single_module, "consistency_validate", _fake_consistency)
    monkeypatch.setattr(run_single_module, "ground_all_fields", _fake_ground)
    monkeypatch.setattr(
        run_single_module,
        "apply_terminal_exact_canonicalization_and_lock",
        lambda state, cfg: None,
    )

    _, audits, _, _, _, _ = run_gse_from_jsonl(str(jsonl_path), cfg)

    assert calls["semantic"] == 1
    assert calls["consistency"] == 1
    assert calls["ground"] == 1
    assert audits[1]["llm_cache_hit"] is True
