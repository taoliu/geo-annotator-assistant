from __future__ import annotations

import sys
import warnings
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agent.config import load_config


def test_example_config_uses_rag_schema() -> None:
    cfg = load_config(str(ROOT / "config" / "example_config.yaml"))
    rag_cfg = cfg.get("rag")
    assert isinstance(rag_cfg, dict)
    assert rag_cfg.get("persist_path") == "ontology_chroma_db"
    assert rag_cfg.get("collection_name") == "ontology_rag"
    assert rag_cfg.get("k") == 20
    ontology_cfg = rag_cfg.get("ontology")
    assert isinstance(ontology_cfg, dict)
    assert ontology_cfg.get("enabled") is False
    assert ontology_cfg.get("canonicalize_terminal_exact_labels") is False
    assert ontology_cfg.get("lock_terminal_exact_fields") is False
    embedding_cfg = ontology_cfg.get("embedding")
    assert isinstance(embedding_cfg, dict)
    assert embedding_cfg.get("device") == "cpu"
    paths_cfg = cfg.get("paths")
    assert isinstance(paths_cfg, dict)
    assert paths_cfg.get("soft_cache_dir") is None
    assert paths_cfg.get("overrides_path") is None


def test_legacy_ontology_keys_map_to_rag(tmp_path: Path) -> None:
    legacy_cfg = {
        "ontology_chroma_enabled": True,
        "ontology_chroma_db_path": "ontology_chroma_db",
        "ontology_chroma_collection": "ontology_rag",
        "ontology_embedding_model_name": "BAAI/bge-base-en-v1.5",
        "ontology_embedding_normalize": True,
        "ontology_top_k": 25,
        "ontology_sources_by_field": {"tissue_type": "Uberon Ontology"},
        "ontology_thresholds": {
            "min_confidence_to_accept": 0.90,
            "max_delta_for_ambiguity": 0.01,
        },
    }
    config_path = tmp_path / "legacy.yaml"
    config_path.write_text(yaml.safe_dump(legacy_cfg), encoding="utf-8")

    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        cfg = load_config(str(config_path))

    assert any(
        "Deprecated config: move ontology_* keys under rag.ontology.*" in str(w.message)
        for w in captured
    )
    rag_cfg = cfg.get("rag")
    assert isinstance(rag_cfg, dict)
    assert rag_cfg.get("persist_path") == "ontology_chroma_db"
    assert rag_cfg.get("collection_name") == "ontology_rag"
    assert rag_cfg.get("k") == 25
    ontology_cfg = rag_cfg.get("ontology")
    assert isinstance(ontology_cfg, dict)
    assert ontology_cfg.get("enabled") is True
    embedding_cfg = ontology_cfg.get("embedding")
    assert isinstance(embedding_cfg, dict)
    assert embedding_cfg.get("model_name") == "BAAI/bge-base-en-v1.5"
    assert embedding_cfg.get("device") == "cpu"
    assert embedding_cfg.get("normalize_embeddings") is True
    thresholds_cfg = ontology_cfg.get("thresholds")
    assert isinstance(thresholds_cfg, dict)
    assert thresholds_cfg.get("min_confidence_to_accept") == 0.90
