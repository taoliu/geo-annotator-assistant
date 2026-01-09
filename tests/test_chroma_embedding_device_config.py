from __future__ import annotations

import sys
from pathlib import Path

import chromadb
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agent.config import load_config
from rag import chroma_client


@pytest.mark.parametrize("device", ["cuda", "mps"])
def test_chroma_embedding_device_passed(monkeypatch, tmp_path: Path, device: str) -> None:
    captured = {}

    class DummyEmbeddingFunction:
        def __init__(self, model_name: str, device: str) -> None:
            captured["model_name"] = model_name
            captured["device"] = device

    monkeypatch.setattr(
        chromadb.utils.embedding_functions,
        "SentenceTransformerEmbeddingFunction",
        DummyEmbeddingFunction,
        raising=True,
    )

    embedding_fn = chroma_client.build_embedding_function(
        model_name="BAAI/bge-base-en-v1.5",
        device=device,
    )

    assert captured["device"] == device
    assert isinstance(embedding_fn, DummyEmbeddingFunction)


def test_invalid_embedding_device_rejected(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "rag": {
                    "ontology": {
                        "embedding": {
                            "device": "tpu",
                        }
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="rag\\.ontology\\.embedding\\.device"):
        load_config(str(config_path))
