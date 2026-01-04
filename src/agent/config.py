"""Configuration loader for the agent."""

from __future__ import annotations

from copy import deepcopy
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

    return _apply_ontology_defaults(data)


_DEFAULT_ONTOLOGY_SOURCES = {
    "tissue_type": "Uberon Ontology",
    "disease": "Human Disease Ontology",
    "cell_line": "Cellosaurus",
    "data_type": "Experimental Factor Ontology",
}

_DEFAULT_ONTOLOGY_THRESHOLDS = {
    "min_confidence_to_accept": 0.80,
    "max_delta_for_ambiguity": 0.05,
}

_DEFAULT_ONTOLOGY_CONFIG = {
    "ontology_chroma_enabled": False,
    "ontology_chroma_db_path": "ontology_chroma_db",
    "ontology_chroma_collection": "ontology_rag",
    "ontology_embedding_model_name": "BAAI/bge-base-en-v1.5",
    "ontology_embedding_normalize": True,
    "ontology_top_k": 20,
    "ontology_sources_by_field": _DEFAULT_ONTOLOGY_SOURCES,
    "ontology_thresholds": _DEFAULT_ONTOLOGY_THRESHOLDS,
}


def _apply_ontology_defaults(config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(config, dict):
        return config

    merged = dict(config)
    for key, value in _DEFAULT_ONTOLOGY_CONFIG.items():
        if key not in merged:
            merged[key] = deepcopy(value)

    sources = merged.get("ontology_sources_by_field")
    if isinstance(sources, dict):
        combined = dict(_DEFAULT_ONTOLOGY_SOURCES)
        combined.update(sources)
        merged["ontology_sources_by_field"] = combined

    thresholds = merged.get("ontology_thresholds")
    if isinstance(thresholds, dict):
        combined = dict(_DEFAULT_ONTOLOGY_THRESHOLDS)
        combined.update(thresholds)
        merged["ontology_thresholds"] = combined

    return merged
