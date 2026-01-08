from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agent.config import load_config


def test_llm_transport_defaults_to_stub(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("versions: {}\n", encoding="utf-8")

    cfg = load_config(str(config_path))

    llm_cfg = cfg.get("llm")
    assert isinstance(llm_cfg, dict)
    assert llm_cfg.get("transport") == "stub"


def test_llm_mode_maps_to_transport(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("llm:\n  mode: local_transformers\n", encoding="utf-8")

    cfg = load_config(str(config_path))

    llm_cfg = cfg.get("llm")
    assert isinstance(llm_cfg, dict)
    assert llm_cfg.get("transport") == "local_transformers"
