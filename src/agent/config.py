"""Configuration loader for the agent."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_config(path: str) -> dict[str, Any]:
    """Load a YAML config file and return the parsed dict."""
    config_path = Path(path)
    if not config_path.is_file():
        raise ValueError(f"Config file not found: {path}")

    try:
        with config_path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in config file: {path}") from exc
    except OSError as exc:
        raise ValueError(f"Unable to read config file: {path}") from exc

    if data is None:
        raise ValueError(f"Config file is empty: {path}")
    if not isinstance(data, dict):
        raise ValueError(f"Config file must contain a top-level mapping: {path}")

    return data
