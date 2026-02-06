from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agent.config import load_config


def test_ingest_defaults_include_missing_policy_and_transport(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("{}", encoding="utf-8")

    cfg = load_config(str(config_path))

    ingest_cfg = cfg.get("ingest")
    assert isinstance(ingest_cfg, dict)
    assert ingest_cfg.get("geo_soft_local_dir") is None
    assert ingest_cfg.get("geo_soft_on_missing") == "remote"
    assert ingest_cfg.get("geo_soft_remote_transport") == "https"


def test_ingest_geo_soft_local_dir_accepts_string(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "ingest:\n  geo_soft_local_dir: /tmp/geo_soft\n",
        encoding="utf-8",
    )

    cfg = load_config(str(config_path))

    ingest_cfg = cfg.get("ingest")
    assert isinstance(ingest_cfg, dict)
    assert ingest_cfg.get("geo_soft_local_dir") == "/tmp/geo_soft"


def test_ingest_geo_soft_local_dir_rejects_non_string(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "ingest:\n  geo_soft_local_dir: 123\n",
        encoding="utf-8",
    )

    try:
        load_config(str(config_path))
    except ValueError as exc:
        assert "ingest.geo_soft_local_dir" in str(exc)
    else:
        raise AssertionError("Expected ValueError for non-string ingest.geo_soft_local_dir")


def test_ingest_geo_soft_on_missing_accepts_allowed_values(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "ingest:\n  geo_soft_on_missing: skip\n",
        encoding="utf-8",
    )

    cfg = load_config(str(config_path))
    ingest_cfg = cfg.get("ingest")
    assert isinstance(ingest_cfg, dict)
    assert ingest_cfg.get("geo_soft_on_missing") == "skip"


def test_ingest_geo_soft_on_missing_rejects_invalid_value(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "ingest:\n  geo_soft_on_missing: maybe\n",
        encoding="utf-8",
    )

    try:
        load_config(str(config_path))
    except ValueError as exc:
        assert "ingest.geo_soft_on_missing" in str(exc)
    else:
        raise AssertionError("Expected ValueError for invalid ingest.geo_soft_on_missing")


def test_ingest_geo_soft_remote_transport_accepts_allowed_values(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "ingest:\n  geo_soft_remote_transport: ftp\n",
        encoding="utf-8",
    )

    cfg = load_config(str(config_path))
    ingest_cfg = cfg.get("ingest")
    assert isinstance(ingest_cfg, dict)
    assert ingest_cfg.get("geo_soft_remote_transport") == "ftp"


def test_ingest_geo_soft_remote_transport_rejects_invalid_value(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "ingest:\n  geo_soft_remote_transport: sftp\n",
        encoding="utf-8",
    )

    try:
        load_config(str(config_path))
    except ValueError as exc:
        assert "ingest.geo_soft_remote_transport" in str(exc)
    else:
        raise AssertionError(
            "Expected ValueError for invalid ingest.geo_soft_remote_transport"
        )
