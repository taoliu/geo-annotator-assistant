"""Configuration loader for the agent."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
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

    merged = _apply_postpass_defaults(
        _apply_paths_defaults(
            _apply_ingest_defaults(_apply_llm_defaults(_apply_rag_defaults(data)))
        )
    )
    _validate_ingest_config(merged)
    _validate_rag_config(merged)
    return merged


@dataclass(frozen=True)
class EmbeddingConfig:
    provider: str = "langchain_huggingface"
    model_name: str = "BAAI/bge-base-en-v1.5"
    device: str = "cpu"
    normalize_embeddings: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "model_name": self.model_name,
            "device": self.device,
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
class NcitFallbackConfig:
    enabled: bool = True
    trigger_terms: list[str] = field(default_factory=lambda: [
        "cancer",
        "tumor",
        "tumour",
        "carcinoma",
        "adenocarcinoma",
        "sarcoma",
        "neoplasm",
        "malignan",
        "metastat",
        "leukemia",
        "lymphoma",
        "myeloma",
        "glioma",
        "glioblastoma",
        "melanoma",
        "blastoma",
    ])

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "trigger_terms": list(self.trigger_terms),
        }


@dataclass(frozen=True)
class DiseaseOntologyConfig:
    ncit_fallback: NcitFallbackConfig = NcitFallbackConfig()

    def to_dict(self) -> dict[str, Any]:
        return {
            "ncit_fallback": self.ncit_fallback.to_dict(),
        }


@dataclass(frozen=True)
class OntologyRagConfig:
    enabled: bool = False
    embedding: EmbeddingConfig = EmbeddingConfig()
    sources_by_field: dict[str, str] = None  # type: ignore[assignment]
    thresholds: ThresholdConfig = ThresholdConfig()
    canonicalize_terminal_exact_labels: bool = False
    lock_terminal_exact_fields: bool = False
    disease: DiseaseOntologyConfig = DiseaseOntologyConfig()

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
            "canonicalize_terminal_exact_labels": self.canonicalize_terminal_exact_labels,
            "lock_terminal_exact_fields": self.lock_terminal_exact_fields,
            "disease": self.disease.to_dict(),
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
_DEFAULT_INGEST_CONFIG = {"geo_soft_local_dir": None}
_DEFAULT_PATHS_CONFIG = {"soft_cache_dir": None, "overrides_path": None}
_DEFAULT_POSTPASS_CONFIG = {
    "gse_consistency": {
        "enabled": True,
        "fields": [
            "data_type",
            "organism",
            "tissue_type",
            "cell_line",
            "disease",
        ],
        "ignore_values": ["Unknown", "None", "No", "Healthy"],
        "outlier_min_samples": 5,
        "outlier_min_dominant_fraction": 0.80,
    },
    "suggestions": {
        "enabled": False,
        "fields": [
            "data_type",
            "organism",
            "tissue_type",
            "cell_line",
            "disease",
            "treatment",
        ],
        "majority_fraction": 0.80,
        "support_fraction_precision": 3,
    },
}
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
_ALLOWED_EMBEDDING_DEVICES = {"cpu", "cuda", "mps"}


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


def _apply_llm_defaults(config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(config, dict):
        return config

    merged = dict(config)
    llm_cfg = merged.get("llm") if isinstance(merged.get("llm"), dict) else {}
    llm_cfg = dict(llm_cfg)
    if "transport" not in llm_cfg:
        if "mode" in llm_cfg:
            llm_cfg["transport"] = llm_cfg.get("mode")
        else:
            llm_cfg["transport"] = "stub"
    merged["llm"] = llm_cfg
    return merged


def _apply_paths_defaults(config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(config, dict):
        return config
    merged = dict(config)
    paths_cfg = merged.get("paths")
    if paths_cfg is None:
        merged["paths"] = dict(_DEFAULT_PATHS_CONFIG)
    elif isinstance(paths_cfg, dict):
        merged["paths"] = _deep_merge(_DEFAULT_PATHS_CONFIG, paths_cfg)
    return merged


def _apply_ingest_defaults(config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(config, dict):
        return config
    merged = dict(config)
    ingest_cfg = merged.get("ingest")
    if ingest_cfg is None:
        merged["ingest"] = dict(_DEFAULT_INGEST_CONFIG)
    elif isinstance(ingest_cfg, dict):
        merged["ingest"] = _deep_merge(_DEFAULT_INGEST_CONFIG, ingest_cfg)
    return merged


def _apply_postpass_defaults(config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(config, dict):
        return config
    merged = dict(config)
    postpass_cfg = merged.get("postpass")
    if postpass_cfg is None:
        merged["postpass"] = _deep_merge(_DEFAULT_POSTPASS_CONFIG, {})
    elif isinstance(postpass_cfg, dict):
        merged["postpass"] = _deep_merge(_DEFAULT_POSTPASS_CONFIG, postpass_cfg)
    return merged


def _validate_rag_config(config: dict[str, Any]) -> None:
    if not isinstance(config, dict):
        return
    rag_cfg = config.get("rag") if isinstance(config.get("rag"), dict) else None
    if not rag_cfg:
        return
    ontology_cfg = (
        rag_cfg.get("ontology")
        if isinstance(rag_cfg.get("ontology"), dict)
        else None
    )
    if not ontology_cfg:
        return
    embedding_cfg = (
        ontology_cfg.get("embedding")
        if isinstance(ontology_cfg.get("embedding"), dict)
        else None
    )
    if not embedding_cfg:
        return
    device = embedding_cfg.get("device", "cpu")
    if device not in _ALLOWED_EMBEDDING_DEVICES:
        raise ValueError(
            "Invalid rag.ontology.embedding.device. "
            f"Expected one of {sorted(_ALLOWED_EMBEDDING_DEVICES)}, got {device!r}."
        )


def _validate_ingest_config(config: dict[str, Any]) -> None:
    if not isinstance(config, dict):
        return
    ingest_cfg = config.get("ingest")
    if ingest_cfg is None:
        return
    if not isinstance(ingest_cfg, dict):
        raise ValueError("Invalid ingest config. Expected a mapping.")
    local_dir = ingest_cfg.get("geo_soft_local_dir")
    if local_dir is None:
        return
    if not isinstance(local_dir, str):
        raise ValueError(
            "Invalid ingest.geo_soft_local_dir. Expected a string or null."
        )
