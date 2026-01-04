"""Configuration loader for the agent."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import warnings

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

    return _apply_rag_defaults(data)


@dataclass(frozen=True)
class EmbeddingConfig:
    provider: str = "langchain_huggingface"
    model_name: str = "BAAI/bge-base-en-v1.5"
    normalize_embeddings: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "model_name": self.model_name,
            "normalize_embeddings": self.normalize_embeddings,
        }


@dataclass(frozen=True)
class ThresholdConfig:
    min_confidence_to_accept: float = 0.80
    max_delta_for_ambiguity: float = 0.05

    def to_dict(self) -> dict[str, Any]:
        return {
            "min_confidence_to_accept": self.min_confidence_to_accept,
            "max_delta_for_ambiguity": self.max_delta_for_ambiguity,
        }


@dataclass(frozen=True)
class OntologyRagConfig:
    enabled: bool = False
    embedding: EmbeddingConfig = EmbeddingConfig()
    sources_by_field: dict[str, str] = None  # type: ignore[assignment]
    thresholds: ThresholdConfig = ThresholdConfig()

    def __post_init__(self):
        if self.sources_by_field is None:
            object.__setattr__(
                self,
                "sources_by_field",
                {
                    "tissue_type": "Uberon Ontology",
                    "disease": "Human Disease Ontology",
                    "cell_line": "Cellosaurus",
                    "data_type": "Experimental Factor Ontology",
                },
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "embedding": self.embedding.to_dict(),
            "sources_by_field": dict(self.sources_by_field),
            "thresholds": self.thresholds.to_dict(),
        }


@dataclass(frozen=True)
class RagConfig:
    persist_path: str = "ontology_chroma_db"
    collection_name: str = "ontology_rag"
    k: int = 20
    ontology: OntologyRagConfig = OntologyRagConfig()

    def to_dict(self) -> dict[str, Any]:
        return {
            "persist_path": self.persist_path,
            "collection_name": self.collection_name,
            "k": self.k,
            "ontology": self.ontology.to_dict(),
        }


_DEFAULT_RAG_CONFIG = RagConfig().to_dict()
_LEGACY_KEYS = {
    "ontology_chroma_enabled",
    "ontology_chroma_db_path",
    "ontology_chroma_collection",
    "ontology_embedding_model_name",
    "ontology_embedding_normalize",
    "ontology_top_k",
    "ontology_sources_by_field",
    "ontology_thresholds",
}


def _deep_merge(base: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _apply_rag_defaults(config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(config, dict):
        return config

    merged = dict(config)
    rag_cfg = merged.get("rag") if isinstance(merged.get("rag"), dict) else {}

    has_legacy = any(key in merged for key in _LEGACY_KEYS)
    rag_ontology = rag_cfg.get("ontology") if isinstance(rag_cfg.get("ontology"), dict) else None
    if has_legacy:
        if rag_ontology:
            warnings.warn(
                "Deprecated config: top-level ontology_* keys are ignored in favor of rag.ontology.*",
                DeprecationWarning,
            )
        else:
            warnings.warn(
                "Deprecated config: move ontology_* keys under rag.ontology.*",
                DeprecationWarning,
            )
            rag_cfg = dict(rag_cfg)
            if merged.get("ontology_chroma_db_path") is not None:
                rag_cfg.setdefault("persist_path", merged.get("ontology_chroma_db_path"))
            if merged.get("ontology_chroma_collection") is not None:
                rag_cfg.setdefault("collection_name", merged.get("ontology_chroma_collection"))
            if merged.get("ontology_top_k") is not None:
                rag_cfg.setdefault("k", merged.get("ontology_top_k"))

            ontology_mapping: dict[str, Any] = {}
            if merged.get("ontology_chroma_enabled") is not None:
                ontology_mapping["enabled"] = merged.get("ontology_chroma_enabled")

            embedding_mapping: dict[str, Any] = {"provider": "langchain_huggingface"}
            if merged.get("ontology_embedding_model_name") is not None:
                embedding_mapping["model_name"] = merged.get("ontology_embedding_model_name")
            if merged.get("ontology_embedding_normalize") is not None:
                embedding_mapping["normalize_embeddings"] = merged.get("ontology_embedding_normalize")
            if len(embedding_mapping) > 1:
                ontology_mapping["embedding"] = embedding_mapping

            if merged.get("ontology_sources_by_field") is not None:
                ontology_mapping["sources_by_field"] = merged.get("ontology_sources_by_field")
            if merged.get("ontology_thresholds") is not None:
                ontology_mapping["thresholds"] = merged.get("ontology_thresholds")
            if ontology_mapping:
                rag_cfg["ontology"] = ontology_mapping

    merged["rag"] = _deep_merge(_DEFAULT_RAG_CONFIG, rag_cfg)
    return merged
