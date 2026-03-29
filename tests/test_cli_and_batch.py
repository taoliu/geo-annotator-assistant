from __future__ import annotations

import sys
from pathlib import Path

import pytest

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


def test_cli_help_includes_verbose(capsys) -> None:
    from agent import cli

    with pytest.raises(SystemExit) as excinfo:
        cli.main(["--help"])

    assert excinfo.value.code == 0
    help_text = capsys.readouterr().out
    assert "--verbose" in help_text
    assert "--overrides" not in help_text


def test_cli_rejects_overrides_option(capsys) -> None:
    from agent import cli

    with pytest.raises(SystemExit) as excinfo:
        cli.main(
            [
                "--gsm",
                "GSM000001",
                "--config",
                str(ROOT / "config" / "example_config.yaml"),
                "--overrides",
                "overrides.jsonl",
            ]
        )

    assert excinfo.value.code == 1
    err = capsys.readouterr().err
    assert "unrecognized arguments: --overrides overrides.jsonl" in err


def test_cli_verbose_disabled_emits_no_runtime_trace(capsys) -> None:
    from agent import cli

    config_path = str(ROOT / "config" / "example_config.yaml")
    cli.main(["--gsm", "GSM000001", "--config", config_path, "--dry-run"])

    stderr = capsys.readouterr().err
    assert "calling LLM for annotation proposal" not in stderr
    assert "validation completed" not in stderr
    assert "ontology grounding started" not in stderr
    assert "decision =" not in stderr


def test_cli_verbose_emits_runtime_trace_for_gsm(capsys) -> None:
    from agent import cli

    config_path = str(ROOT / "config" / "example_config.yaml")
    cli.main(
        [
            "--gsm",
            "GSM000001",
            "--config",
            config_path,
            "--dry-run",
            "--verbose",
        ]
    )

    stderr = capsys.readouterr().err
    assert "INFO: GSM000001: calling LLM for annotation proposal" in stderr
    assert "INFO: GSM000001: LLM proposal received" in stderr
    assert "INFO: GSM000001: validation completed" in stderr
    assert "INFO: GSM000001: ontology grounding started" in stderr
    assert "INFO: GSM000001: ontology grounding completed" in stderr
    assert "INFO: GSM000001: decision = ACCEPT" in stderr


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

    def _fake_run_gse_from_accession(
        gse_accession: str,
        cfg: dict,
        work_dir: str,
        llm_client=None,
    ):
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


def test_cli_verbose_gse_file_emits_start_and_output_messages(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    from agent import cli

    config_path = str(ROOT / "config" / "example_config.yaml")
    gse_file = tmp_path / "gse_list.txt"
    gse_file.write_text("GSE311\nGSE312\n", encoding="utf-8")

    def _fake_run_gse_from_accession(
        gse_accession: str,
        cfg: dict,
        work_dir: str,
        llm_client=None,
    ):
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
            "--verbose",
        ]
    )

    stderr = capsys.readouterr().err
    for gse in ("GSE311", "GSE312"):
        expected_dir = tmp_path / "out" / gse
        assert f"INFO: {gse}: start processing" in stderr
        assert f"INFO: {gse}: outputs written to {expected_dir}" in stderr


def test_cli_gse_file_reuses_llm_client(tmp_path: Path, monkeypatch) -> None:
    from agent import cli

    config_path = str(ROOT / "config" / "example_config.yaml")
    gse_file = tmp_path / "gse_list.txt"
    gse_file.write_text("GSE901\nGSE902\n", encoding="utf-8")

    sentinel = object()
    counts = {"created": 0}
    calls: list[object] = []

    def _fake_create_llm_client(_cfg: dict):
        counts["created"] += 1
        return sentinel

    def _fake_run_gse_from_accession(
        gse_accession: str,
        cfg: dict,
        work_dir: str,
        llm_client=None,
    ):
        calls.append(llm_client)
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

    def _fake_load_config(_path: str) -> dict:
        return {"llm": {"transport": "local_transformers"}}

    monkeypatch.setattr(cli, "create_llm_client", _fake_create_llm_client)
    monkeypatch.setattr(cli, "run_gse_from_accession", _fake_run_gse_from_accession)
    monkeypatch.setattr(cli, "load_config", _fake_load_config)

    cli.main(
        [
            "--gse-file",
            str(gse_file),
            "--config",
            config_path,
            "--dry-run",
        ]
    )

    assert counts["created"] == 1
    assert calls == [sentinel, sentinel]


def test_cli_single_gse_builds_llm_client_once(tmp_path: Path, monkeypatch) -> None:
    from agent import cli

    config_path = str(ROOT / "config" / "example_config.yaml")

    sentinel = object()
    counts = {"created": 0}
    calls: list[object] = []

    def _fake_create_llm_client(_cfg: dict):
        counts["created"] += 1
        return sentinel

    def _fake_run_gse_from_accession(
        gse_accession: str,
        cfg: dict,
        work_dir: str,
        llm_client=None,
    ):
        calls.append(llm_client)
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

    def _fake_load_config(_path: str) -> dict:
        return {"llm": {"transport": "local_transformers"}}

    monkeypatch.setattr(cli, "create_llm_client", _fake_create_llm_client)
    monkeypatch.setattr(cli, "run_gse_from_accession", _fake_run_gse_from_accession)
    monkeypatch.setattr(cli, "load_config", _fake_load_config)

    cli.main(
        [
            "--gse",
            "GSE777",
            "--config",
            config_path,
            "--dry-run",
        ]
    )

    assert counts["created"] == 1
    assert calls == [sentinel]


def test_cli_gse_file_skips_reuse_for_nonlocal(tmp_path: Path, monkeypatch) -> None:
    from agent import cli

    config_path = str(ROOT / "config" / "example_config.yaml")
    gse_file = tmp_path / "gse_list.txt"
    gse_file.write_text("GSE801\nGSE802\n", encoding="utf-8")

    counts = {"created": 0}
    calls: list[object] = []

    def _fake_create_llm_client(_cfg: dict):
        counts["created"] += 1
        return object()

    def _fake_load_config(_path: str) -> dict:
        return {"llm": {"transport": "openai_http"}}

    def _fake_run_gse_from_accession(
        gse_accession: str,
        cfg: dict,
        work_dir: str,
        llm_client=None,
    ):
        calls.append(llm_client)
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

    monkeypatch.setattr(cli, "create_llm_client", _fake_create_llm_client)
    monkeypatch.setattr(cli, "load_config", _fake_load_config)
    monkeypatch.setattr(cli, "run_gse_from_accession", _fake_run_gse_from_accession)

    cli.main(
        [
            "--gse-file",
            str(gse_file),
            "--config",
            config_path,
            "--dry-run",
        ]
    )

    assert counts["created"] == 0
    assert calls == [None, None]


def test_cli_gse_file_skips_missing_local_soft(tmp_path: Path, monkeypatch, capsys) -> None:
    from agent import cli
    from ingest.soft_to_context_jsonl import LocalSoftMissingError

    config_path = str(ROOT / "config" / "example_config.yaml")
    gse_file = tmp_path / "gse_list.txt"
    gse_file.write_text("GSE111\nGSE222\n", encoding="utf-8")

    def _fake_run_gse_from_accession(
        gse_accession: str,
        cfg: dict,
        work_dir: str,
        llm_client=None,
    ):
        if gse_accession == "GSE111":
            raise LocalSoftMissingError(
                gse_accession,
                "/mirror/GSEnnn/GSE111_family.soft.gz",
            )
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

    warning = capsys.readouterr().err
    assert "WARNING: GEO SOFT file not found for GSE111" in warning
    assert (tmp_path / "out" / "GSE222" / "annotations.jsonl").exists()


def test_cli_gse_file_skips_no_sample_local_soft(tmp_path: Path, monkeypatch, capsys) -> None:
    from agent import cli
    from ingest.soft_to_context_jsonl import LocalSoftNoSampleDataError

    config_path = str(ROOT / "config" / "example_config.yaml")
    gse_file = tmp_path / "gse_list.txt"
    gse_file.write_text("GSE111\nGSE222\n", encoding="utf-8")

    def _fake_run_gse_from_accession(
        gse_accession: str,
        cfg: dict,
        work_dir: str,
        llm_client=None,
    ):
        if gse_accession == "GSE111":
            raise LocalSoftNoSampleDataError(
                gse_accession,
                "/mirror/GSEnnn/GSE111_family.soft.gz",
            )
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

    warning = capsys.readouterr().err
    assert "WARNING: GEO SOFT file for GSE111" in warning
    assert "contains no sample data; skipping." in warning
    assert (tmp_path / "out" / "GSE222" / "annotations.jsonl").exists()


def test_cli_gse_soft_skips_no_sample_soft_file(tmp_path: Path, monkeypatch, capsys) -> None:
    from agent import cli
    from ingest.soft_to_context_jsonl import SoftNoSampleDataError

    config_path = str(ROOT / "config" / "example_config.yaml")
    soft_path = tmp_path / "GSE111_family.soft.gz"
    soft_path.write_text("VALID-BUT-EMPTY", encoding="utf-8")

    def _fake_run_gse_from_soft_file(
        soft_file: str,
        cfg: dict,
        work_dir: str,
        llm_client=None,
    ):
        raise SoftNoSampleDataError(soft_file, gse_accession="GSE111")

    monkeypatch.setattr(cli, "run_gse_from_soft_file", _fake_run_gse_from_soft_file)

    cli.main(
        [
            "--gse-soft",
            str(soft_path),
            "--config",
            config_path,
            "--output-dir",
            str(tmp_path / "out"),
        ]
    )

    warning = capsys.readouterr().err
    assert "WARNING: GEO SOFT file for GSE111" in warning
    assert "contains no sample data; skipping." in warning
    assert not (tmp_path / "out" / "annotations.jsonl").exists()
