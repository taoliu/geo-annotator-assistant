from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agent.config import load_config
from agent.run_batch import run_batch
from agent.writer import write_run_outputs


def _load_stub_config() -> dict:
    cfg = load_config(str(ROOT / "config" / "example_config.yaml"))
    cfg.setdefault("parser", {})["mode"] = "stub"
    cfg.setdefault("llm", {})["mode"] = "stub"
    return cfg


def test_run_batch_stub_two_gsms() -> None:
    cfg = _load_stub_config()
    annotations, audits, flagged, summary = run_batch(
        ["GSM000001", "GSM000002"], cfg
    )

    assert summary["n_total"] == 2
    assert summary["n_flagged"] == 0
    assert summary["n_accepted"] == 2
    assert len(annotations) == 2
    assert len(audits) == 2
    assert flagged == []


def test_run_batch_handles_failure(monkeypatch) -> None:
    cfg = _load_stub_config()
    gsms = ["GSM000001", "GSMFAIL"]

    import agent.run_batch as run_batch_module

    original_run_single = run_batch_module.run_single_gsm

    def _fake_run_single(gsm_accession: str, cfg: dict):
        if gsm_accession == "GSMFAIL":
            raise RuntimeError("boom")
        return original_run_single(gsm_accession, cfg)

    monkeypatch.setattr(run_batch_module, "run_single_gsm", _fake_run_single)

    annotations, audits, flagged, summary = run_batch_module.run_batch(gsms, cfg)

    assert summary["n_total"] == 2
    assert summary["n_flagged"] == 1
    assert summary["n_accepted"] == 1
    assert len(annotations) == 2
    assert len(audits) == 2
    assert len(flagged) == 1
    assert flagged[0]["gsm_accession"] == "GSMFAIL"
    assert audits[1]["final_decision"] == "FLAGGED"
    assert audits[1]["error"] == "boom"


def test_writer_integration(tmp_path: Path) -> None:
    cfg = _load_stub_config()
    annotations, audits, flagged, _ = run_batch(["GSM000001", "GSM000002"], cfg)

    output_paths = write_run_outputs(str(tmp_path), annotations, audits, flagged)

    for key, expected_count in {
        "annotations": len(annotations),
        "audit": len(audits),
        "flagged": len(flagged),
    }.items():
        path = Path(output_paths[key])
        assert path.exists()
        assert len(path.read_text(encoding="utf-8").splitlines()) == expected_count

    curation_path = Path(output_paths["curation"])
    assert curation_path.exists()
    assert len(curation_path.read_text(encoding="utf-8").splitlines()) == (
        len(audits) + 1
    )


def test_cli_dry_run_prints_summary(capsys) -> None:
    from agent import cli

    config_path = str(ROOT / "config" / "example_config.yaml")
    cli.main(["--gsm", "GSM000001", "--config", config_path, "--dry-run"])

    output = capsys.readouterr().out
    assert "Total: 1" in output
    assert "Dry-run: no files written" in output
