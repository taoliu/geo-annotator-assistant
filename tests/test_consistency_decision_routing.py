from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agent.config import load_config
from agent.repair_loop import apply_repairs
from agent.run_gse import run_gse_from_jsonl
from agent.state import PipelineState
from validator.decision_engine import load_decision_table


def _decision_table() -> dict:
    return load_decision_table(str(ROOT / "spec" / "decision_table.yaml"))


def _load_stub_config() -> dict:
    cfg = load_config(str(ROOT / "config" / "example_config.yaml"))
    cfg.setdefault("parser", {})["mode"] = "stub"
    cfg.setdefault("llm", {})["transport"] = "stub"
    return cfg


def test_healthy_disease_conflict_fallback() -> None:
    state = PipelineState(
        gsm_accession="GSM000",
        final_output={"disease": "Healthy"},
        semantic_errors={"disease": ["healthy_disease_conflict"]},
        consistency_flags=["healthy_disease_conflict"],
    )
    result = apply_repairs(state, _decision_table())
    assert result.final_decision == "ACCEPT"
    assert result.final_output["disease"] == "Unknown"


def test_organism_context_conflict_escalates() -> None:
    state = PipelineState(
        gsm_accession="GSM001",
        final_output={"organism": "Homo sapiens"},
        semantic_errors={"organism": ["organism_context_conflict"]},
        consistency_flags=["organism_context_conflict"],
    )
    result = apply_repairs(state, _decision_table())
    assert result.final_decision == "FLAGGED"
    assert "organism_context_conflict" in result.flags


def test_jsonl_stub_does_not_auto_flag_consistency(tmp_path: Path) -> None:
    cfg = _load_stub_config()
    record = {
        "gse_accession": "GSE123456",
        "gsm_accession": "GSM123456",
        "context_text": "Cancer samples were profiled using RNA-seq.",
    }
    jsonl_path = tmp_path / "contexts.jsonl"
    jsonl_path.write_text(json.dumps(record) + "\n", encoding="utf-8")

    annotations, audits, flagged, summary, _ = run_gse_from_jsonl(
        str(jsonl_path), cfg
    )

    assert summary["n_total"] == 1
    assert summary["n_flagged"] == 0
    assert summary["n_accepted"] == 1
    assert flagged == []
    assert annotations[0]["disease"] == "Unknown"
    assert audits[0]["final_decision"] == "ACCEPT"
