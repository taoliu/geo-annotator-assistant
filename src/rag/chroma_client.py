from __future__ import annotations
from typing import Any
import os

def get_chroma_client(persist_path: str) -> Any:
    """Create a ChromaDB client from a local persist directory."""
    if not persist_path or not os.path.isdir(persist_path):
        raise ValueError(f"Chroma persist_path not found: {persist_path!r}")
    # Lazy import so other modules can import without chromadb installed in some contexts.
    import chromadb
    return chromadb.PersistentClient(path=persist_path)


def get_chroma_collection(
    persist_path: str,
    collection_name: str,
) -> Any:
    """Open a persisted Chroma collection without an embedding function."""
    client = get_chroma_client(persist_path)
    return client.get_collection(name=collection_name)


def build_embedding_function(
    model_name: str = "BAAI/bge-base-en-v1.5",
    device: str = "cpu",
) -> Any:
    """Build an embedding function for explicit query embeddings."""
    from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
    return SentenceTransformerEmbeddingFunction(
        model_name=model_name,
        device=device,
    )
