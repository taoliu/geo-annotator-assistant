from __future__ import annotations

import sys
from pathlib import Path

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
        get_local_path("GSE1234", "/mirror")
        == "/mirror/GSE1nnn/GSE1234_family.soft.gz"
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
