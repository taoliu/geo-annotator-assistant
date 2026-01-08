from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agent.config import load_config
from agent.run_single import run_single_gsm

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


def _load_stub_config() -> dict:
    cfg = load_config(str(ROOT / "config" / "example_config.yaml"))
    cfg.setdefault("parser", {})["mode"] = "stub"
    cfg.setdefault("llm", {})["transport"] = "stub"
    return cfg


def test_run_single_stub_accepts() -> None:
    cfg = _load_stub_config()
    primary_output, audit_record, flagged = run_single_gsm("GSM000000", cfg)

    assert set(primary_output.keys()) == REQUIRED_KEYS
    assert flagged is False
    assert audit_record["gsm_accession"] == "GSM000000"
    validation = audit_record["validation"]
    for key in (
        "format_errors",
        "semantic_errors",
        "consistency_flags",
        "ontology_matches",
        "ontology_failures",
    ):
        assert key in validation


def test_run_single_invalid_json_flagged() -> None:
    cfg = _load_stub_config()
    cfg["llm"]["stub_invalid_json"] = True
    _, audit_record, flagged = run_single_gsm("GSM000000", cfg)

    assert flagged is True
    assert audit_record["final_decision"] == "FLAGGED"
