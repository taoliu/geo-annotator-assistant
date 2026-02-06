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
    cfg.setdefault("llm", {})["transport"] = "stub"
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

    def _fake_run_single(gsm_accession: str, cfg: dict, llm_client=None):
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

    curation_jsonl_path = Path(output_paths["curation_jsonl"])
    assert curation_jsonl_path.exists()
    assert len(curation_jsonl_path.read_text(encoding="utf-8").splitlines()) == len(
        audits
    )

    evidence_path = Path(output_paths["evidence"])
    assert evidence_path.exists()
    assert len(evidence_path.read_text(encoding="utf-8").splitlines()) == len(audits)


def test_cli_dry_run_prints_summary(capsys) -> None:
    from agent import cli

    config_path = str(ROOT / "config" / "example_config.yaml")
    cli.main(["--gsm", "GSM000001", "--config", config_path, "--dry-run"])

    output = capsys.readouterr().out
    assert "Total: 1" in output
    assert "Dry-run: no files written" in output


def test_cli_no_suggestions_file(tmp_path: Path) -> None:
    from agent import cli

    config_path = str(ROOT / "config" / "example_config.yaml")
    cli.main(
        [
            "--gsm",
            "GSM000001",
            "--config",
            config_path,
            "--output-dir",
            str(tmp_path),
        ]
    )

    assert not (tmp_path / "suggestions.jsonl").exists()


def test_read_gse_file_dedupes_and_ignores_comments(tmp_path: Path) -> None:
    from agent import cli

    gse_file = tmp_path / "gse_list.txt"
    gse_file.write_text(
        "\n".join(
            [
                "# comment",
                " GSE001 ",
                "",
                "GSE002",
                "GSE001",
                "   # another comment",
                "GSE003",
            ]
        ),
        encoding="utf-8",
    )

    assert cli._read_gse_file(str(gse_file)) == ["GSE001", "GSE002", "GSE003"]


def test_cli_gse_file_outputs_per_gse(tmp_path: Path, monkeypatch) -> None:
    from agent import cli

    config_path = str(ROOT / "config" / "example_config.yaml")
    gse_file = tmp_path / "gse_list.txt"
    gse_file.write_text("GSE111\nGSE222\n", encoding="utf-8")

    calls: list[str] = []

    def _fake_run_gse_from_accession(gse_accession: str, cfg: dict, work_dir: str):
        calls.append(gse_accession)
        annotation = {
            "gse_accession": gse_accession,
            "gsm_accession": f"{gse_accession}_GSM1",
            "data_type": "Unknown",
            "organism": "Unknown",
            "tissue_type": "Unknown",
            "cell_line": "No",
            "disease": "Healthy",
            "treatment": "None",
        }
        audit = {
            "gse_accession": gse_accession,
            "gsm_accession": f"{gse_accession}_GSM1",
            "final_decision": "ACCEPTED",
            "final_output": dict(annotation),
            "rationale": {
                "final_decision": "ACCEPTED",
                "primary_failure": None,
                "terminal_fallback_fields": [],
                "n_llm_calls": 0,
                "attempts_by_field": {},
                "ontology_status_by_field": {},
                "flags": [],
            },
        }
        summary = {"n_total": 1, "n_accepted": 1, "n_flagged": 0}
        return [annotation], [audit], [], summary, None, None

    monkeypatch.setattr(cli, "run_gse_from_accession", _fake_run_gse_from_accession)

    cli.main(
        [
            "--gse-file",
            str(gse_file),
            "--config",
            config_path,
            "--output-dir",
            str(tmp_path / "out"),
        ]
    )

    assert calls == ["GSE111", "GSE222"]
    for gse in calls:
        output_dir = tmp_path / "out" / gse
        assert (output_dir / "annotations.jsonl").exists()
        assert (output_dir / "audit.jsonl").exists()
