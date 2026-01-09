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
    persist_path = tmp_path / "ontology_chroma_db"
    persist_path.mkdir()

    captured = {}

    class DummyEmbeddingFunction:
        def __init__(self, model_name: str, device: str) -> None:
            captured["model_name"] = model_name
            captured["device"] = device

    class FakeClient:
        def get_collection(self, name, embedding_function=None):
            captured["collection_name"] = name
            captured["embedding_function"] = embedding_function
            return "collection"

    monkeypatch.setattr(
        chromadb,
        "PersistentClient",
        lambda *args, **kwargs: FakeClient(),
        raising=True,
    )
    monkeypatch.setattr(
        chromadb.utils.embedding_functions,
        "SentenceTransformerEmbeddingFunction",
        DummyEmbeddingFunction,
        raising=True,
    )

    collection = chroma_client.get_chroma_collection(
        str(persist_path),
        "ontology_rag",
        model_name="BAAI/bge-base-en-v1.5",
        device=device,
    )

    assert collection == "collection"
    assert captured["device"] == device
    assert isinstance(captured["embedding_function"], DummyEmbeddingFunction)


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
