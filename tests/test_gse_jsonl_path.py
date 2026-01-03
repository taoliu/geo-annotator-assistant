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


def _load_stub_config() -> dict:
    cfg = load_config(str(ROOT / "config" / "example_config.yaml"))
    cfg.setdefault("llm", {})["mode"] = "stub"
    return cfg


def _write_jsonl(path: Path, records: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record))
            handle.write("\n")


def test_run_gse_from_jsonl_stub(tmp_path: Path) -> None:
    records = [
        {
            "context_text": "Series Accession: GSE123\nSample ID: GSM001",
            "gsm_accession": "GSM001",
            "gse_accession": "GSE123",
        },
        {
            "context_text": "Series Accession: GSE123\nSample ID: GSM002",
            "gsm_accession": "GSM002",
            "gse_accession": "GSE123",
        },
    ]
    jsonl_path = tmp_path / "contexts.jsonl"
    _write_jsonl(jsonl_path, records)

    cfg = _load_stub_config()
    annotations, audits, flagged, summary = run_gse_from_jsonl(str(jsonl_path), cfg)

    assert summary["n_total"] == 2
    assert summary["n_flagged"] == 0
    assert summary["n_accepted"] == 2
    assert [row["gsm_accession"] for row in annotations] == ["GSM001", "GSM002"]
    assert {row["gse_accession"] for row in annotations} == {"GSE123"}
    assert flagged == []
    assert len(audits) == 2


def test_run_gse_from_jsonl_raises_on_missing_key(tmp_path: Path) -> None:
    records = [
        {
            "context_text": "Series Accession: GSE123\nSample ID: GSM001",
            "gsm_accession": "GSM001",
            "gse_accession": "GSE123",
        },
        {
            "gsm_accession": "GSM002",
            "gse_accession": "GSE123",
        },
    ]
    jsonl_path = tmp_path / "bad.jsonl"
    _write_jsonl(jsonl_path, records)

    cfg = _load_stub_config()
    with pytest.raises(ValueError, match="Line 2"):
        run_gse_from_jsonl(str(jsonl_path), cfg)


def test_cli_jsonl_dry_run(capsys, tmp_path: Path) -> None:
    from agent import cli

    records = [
        {
            "context_text": "Series Accession: GSE123\nSample ID: GSM001",
            "gsm_accession": "GSM001",
            "gse_accession": "GSE123",
        },
        {
            "context_text": "Series Accession: GSE123\nSample ID: GSM002",
            "gsm_accession": "GSM002",
            "gse_accession": "GSE123",
        },
    ]
    jsonl_path = tmp_path / "contexts.jsonl"
    _write_jsonl(jsonl_path, records)

    config_path = str(ROOT / "config" / "example_config.yaml")
    cli.main(["--jsonl", str(jsonl_path), "--config", config_path, "--dry-run"])

    output = capsys.readouterr().out
    assert "Total: 2" in output
    assert "Dry-run: no files written" in output
