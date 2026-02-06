from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import ingest.soft_to_context_jsonl as soft_module
from agent.config import load_config
from agent.run_gse import run_gse_from_accession, run_gse_from_soft_file
from ingest.gse_soft_fetcher import get_local_path


def _load_stub_config() -> dict:
    cfg = load_config(str(ROOT / "config" / "example_config.yaml"))
    cfg.setdefault("parser", {})["mode"] = "stub"
    cfg.setdefault("llm", {})["transport"] = "stub"
    cfg.setdefault("rag", {}).setdefault("ontology", {})["enabled"] = False
    return cfg


def _fake_gse_dict(gse_accession: str, gsm_accession: str) -> dict:
    return {
        gsm_accession: {
            "series": {"series gse accession": gse_accession},
            "platform": [{"platform title": "Test Platform"}],
            "sample_data": {"sample title": "Test Sample"},
        }
    }


def _patch_parser(monkeypatch, gse_accession: str, gsm_accession: str) -> None:
    def _fake_extract(_path: str):
        return _fake_gse_dict(gse_accession, gsm_accession)

    monkeypatch.setattr(soft_module, "extract_sample_level_data", _fake_extract)


def test_run_gse_from_soft_file_local_path(
    tmp_path: Path,
    monkeypatch,
) -> None:
    soft_path = tmp_path / "GSE999.soft"
    soft_path.write_text("FAKE SOFT", encoding="utf-8")

    _patch_parser(monkeypatch, "GSE999", "GSM001")
    cfg = _load_stub_config()
    annotations, audits, flagged, summary, report, values = run_gse_from_soft_file(
        str(soft_path),
        cfg,
        str(tmp_path),
    )

    assert summary["n_total"] == 1
    assert summary["n_accepted"] == 1
    assert summary["n_flagged"] == 0
    assert len(annotations) == 1
    assert annotations[0]["gse_accession"] == "GSE999"
    assert annotations[0]["gsm_accession"] == "GSM001"
    assert flagged == []
    assert len(audits) == 1
    assert report is not None
    assert values is not None


def test_run_gse_from_accession_uses_cache(
    tmp_path: Path,
    monkeypatch,
) -> None:
    gse_accession = "GSE123"
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    cached_soft = cache_dir / f"{gse_accession}_family.soft.gz"
    cached_soft.write_text("FAKE SOFT", encoding="utf-8")

    _patch_parser(monkeypatch, gse_accession, "GSM002")

    def _no_download(*_args, **_kwargs):
        raise AssertionError("download should not be called when cache exists")

    monkeypatch.setattr(soft_module, "download_file_via_https", _no_download)

    cfg = _load_stub_config()
    cfg.setdefault("paths", {})["soft_cache_dir"] = str(cache_dir)
    annotations, _, flagged, summary, _, _ = run_gse_from_accession(
        gse_accession,
        cfg,
        str(tmp_path),
    )

    assert summary["n_total"] == 1
    assert summary["n_accepted"] == 1
    assert summary["n_flagged"] == 0
    assert annotations[0]["gse_accession"] == gse_accession
    assert annotations[0]["gsm_accession"] == "GSM002"
    assert flagged == []


def test_get_local_path_mapping() -> None:
    assert (
        get_local_path("GSE1", "/mirror")
        == "/mirror/GSEnnn/GSE1_family.soft.gz"
    )
    assert (
        get_local_path("GSE999", "/mirror")
        == "/mirror/GSEnnn/GSE999_family.soft.gz"
    )
    assert (
        get_local_path("GSE1000", "/mirror")
        == "/mirror/GSE1nnn/GSE1000_family.soft.gz"
    )
    assert (
        get_local_path("GSE1234", "/mirror")
        == "/mirror/GSE1nnn/GSE1234_family.soft.gz"
    )
    assert (
        get_local_path("GSE25001", "/mirror")
        == "/mirror/GSE25nnn/GSE25001_family.soft.gz"
    )


def test_run_gse_from_accession_uses_local_mirror(
    tmp_path: Path,
    monkeypatch,
) -> None:
    gse_accession = "GSE777"
    local_dir = tmp_path / "mirror"
    local_dir.mkdir()
    local_path = Path(get_local_path(gse_accession, str(local_dir)))
    local_path.parent.mkdir(parents=True, exist_ok=True)
    local_path.write_text("FAKE SOFT", encoding="utf-8")

    _patch_parser(monkeypatch, gse_accession, "GSM777")

    def _no_download(*_args, **_kwargs):
        raise AssertionError("download should not be called when local mirror exists")

    monkeypatch.setattr(soft_module, "download_file_via_https", _no_download)
    monkeypatch.setattr(soft_module, "download_file_via_ftp", _no_download)

    cfg = _load_stub_config()
    cfg.setdefault("ingest", {})["geo_soft_local_dir"] = str(local_dir)
    annotations, _, flagged, summary, _, _ = run_gse_from_accession(
        gse_accession,
        cfg,
        str(tmp_path),
    )

    assert summary["n_total"] == 1
    assert summary["n_accepted"] == 1
    assert summary["n_flagged"] == 0
    assert annotations[0]["gse_accession"] == gse_accession
    assert annotations[0]["gsm_accession"] == "GSM777"
    assert flagged == []


@pytest.mark.parametrize(
    ("remote_transport", "called_transport"),
    [
        ("https", "https"),
        ("ftp", "ftp"),
    ],
)
def test_remote_transport_selection_for_download(
    tmp_path: Path,
    monkeypatch,
    remote_transport: str,
    called_transport: str,
) -> None:
    gse_accession = "GSE888"
    _patch_parser(monkeypatch, gse_accession, "GSM888")
    calls: list[str] = []

    def _https_download(_remote: str, local: str, **_kwargs) -> None:
        calls.append("https")
        local_path = Path(local)
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_text("FAKE SOFT", encoding="utf-8")

    def _ftp_download(_remote: str, local: str, **_kwargs) -> None:
        calls.append("ftp")
        local_path = Path(local)
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_text("FAKE SOFT", encoding="utf-8")

    monkeypatch.setattr(soft_module, "download_file_via_https", _https_download)
    monkeypatch.setattr(soft_module, "download_file_via_ftp", _ftp_download)

    jsonl_path = soft_module.soft_to_context_jsonl(
        gse_accession=gse_accession,
        work_dir=tmp_path,
        geo_soft_remote_transport=remote_transport,
    )

    assert calls == [called_transport]
    assert Path(jsonl_path).is_file()


def test_local_miss_skip_raises_and_does_not_download(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    gse_accession = "GSE321"
    local_dir = tmp_path / "mirror"

    def _no_download(*_args, **_kwargs):
        raise AssertionError("download should not be called when on_missing=skip")

    monkeypatch.setattr(soft_module, "download_file_via_https", _no_download)
    monkeypatch.setattr(soft_module, "download_file_via_ftp", _no_download)

    with pytest.raises(soft_module.LocalSoftMissingError):
        soft_module.soft_to_context_jsonl(
            gse_accession=gse_accession,
            work_dir=tmp_path,
            geo_soft_local_dir=local_dir,
            geo_soft_on_missing="skip",
        )

    stderr = capsys.readouterr().err
    assert f"INFO: {gse_accession}: resolving SOFT (local-first)" in stderr
    assert (
        f"WARNING: {gse_accession}: local SOFT missing at "
        in stderr
    )
    assert "geo_soft_on_missing=skip" in stderr


def test_local_miss_error_raises_and_does_not_download(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    gse_accession = "GSE654"
    local_dir = tmp_path / "mirror"

    def _no_download(*_args, **_kwargs):
        raise AssertionError("download should not be called when on_missing=error")

    monkeypatch.setattr(soft_module, "download_file_via_https", _no_download)
    monkeypatch.setattr(soft_module, "download_file_via_ftp", _no_download)

    with pytest.raises(FileNotFoundError):
        soft_module.soft_to_context_jsonl(
            gse_accession=gse_accession,
            work_dir=tmp_path,
            geo_soft_local_dir=local_dir,
            geo_soft_on_missing="error",
        )

    stderr = capsys.readouterr().err
    assert f"INFO: {gse_accession}: resolving SOFT (local-first)" in stderr
    assert (
        f"ERROR: {gse_accession}: local SOFT missing at "
        in stderr
    )
    assert "geo_soft_on_missing=error" in stderr


def test_local_miss_remote_downloads_to_local_mirror(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    gse_accession = "GSE4321"
    local_dir = tmp_path / "mirror"
    _patch_parser(monkeypatch, gse_accession, "GSM4321")
    calls: list[str] = []

    def _ftp_download(_remote: str, local: str, **_kwargs) -> None:
        calls.append("ftp")
        local_path = Path(local)
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_text("FAKE SOFT", encoding="utf-8")

    def _https_download(*_args, **_kwargs) -> None:
        raise AssertionError("https downloader should not be called when transport=ftp")

    monkeypatch.setattr(soft_module, "download_file_via_https", _https_download)
    monkeypatch.setattr(soft_module, "download_file_via_ftp", _ftp_download)

    jsonl_path = soft_module.soft_to_context_jsonl(
        gse_accession=gse_accession,
        work_dir=tmp_path,
        geo_soft_local_dir=local_dir,
        geo_soft_on_missing="remote",
        geo_soft_remote_transport="ftp",
    )

    expected_local = Path(get_local_path(gse_accession, str(local_dir)))
    assert expected_local.is_file()
    assert Path(jsonl_path).is_file()
    assert calls == ["ftp"]

    stderr = capsys.readouterr().err
    assert f"INFO: {gse_accession}: resolving SOFT (local-first)" in stderr
    assert f"WARNING: {gse_accession}: local SOFT missing at {expected_local}; downloading via ftp" in stderr
    assert f"INFO: {gse_accession}: downloaded SOFT to {expected_local}" in stderr
