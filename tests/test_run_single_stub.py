from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agent.config import load_config
from agent.runtime_trace import tracing_scope
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
        "format_error_details",
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


def test_verbose_repair_loop_messages_emitted(monkeypatch, capsys) -> None:
    cfg = _load_stub_config()

    import agent.run_single as run_single_module

    def _fake_update_validation_state(state, _parsed_output, _context_text, _cfg) -> None:
        state.semantic_errors = {"disease": ["mock_failure"]}
        state.ontology_failures = {}
        state.consistency_flags = []

    def _fake_apply_repairs(state, *_args, **_kwargs):
        state.semantic_errors = {}
        state.ontology_failures = {}
        state.consistency_flags = []
        state.final_decision = "ACCEPT"
        return state

    monkeypatch.setattr(
        run_single_module,
        "_update_validation_state",
        _fake_update_validation_state,
    )
    monkeypatch.setattr(run_single_module, "apply_repairs", _fake_apply_repairs)

    with tracing_scope(True):
        run_single_gsm("GSM000123", cfg)

    stderr = capsys.readouterr().err
    assert "INFO: GSM000123: entering repair loop" in stderr
    assert "INFO: GSM000123: repair loop completed" in stderr
