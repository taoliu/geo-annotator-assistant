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
from llm.factory import create_llm_client

REQUIRED_KEYS = {
    "gse_accession",
    "gsm_accession",
    "data_type",
    "organism",
    "tissue_type",
    "cell_line",
    "disease",
    "treatment",
}


def test_factory_returns_stub_client() -> None:
    client = create_llm_client({"mode": "stub"})
    assert client.__class__.__name__ == "StubLLMClient"


def test_stub_generate_returns_valid_json() -> None:
    client = create_llm_client({"mode": "stub"})
    prompt = "Series Accession: GSE123456\nSample ID: GSM654321\n"
    output = client.generate(prompt)
    parsed = json.loads(output)

    assert set(parsed.keys()) == REQUIRED_KEYS
    assert parsed["gse_accession"] == "GSE123456"
    assert parsed["gsm_accession"] == "GSM654321"


def test_run_single_from_context_record_stub_smoke() -> None:
    cfg = load_config(str(ROOT / "config" / "example_config.yaml"))
    cfg.setdefault("llm", {})["mode"] = "stub"

    record = {
        "gsm_accession": "GSM000111",
        "gse_accession": "GSE000222",
        "context_text": (
            "Series Accession: GSE000222\n"
            "Sample ID: GSM000111\n"
            "Sample Organism: Homo sapiens\n"
        ),
    }

    output, audit_record, flagged = run_single_from_context_record(record, cfg)

    assert output["gsm_accession"] == "GSM000111"
    assert audit_record["gsm_accession"] == "GSM000111"
    assert flagged is False
