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
    model_name: str = "BAAI/bge-base-en-v1.5",
    device: str = "cpu",
) -> Any:
    """Open a persisted Chroma collection with a direct embedding function."""
    client = get_chroma_client(persist_path)
    from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

    embedding_function = SentenceTransformerEmbeddingFunction(
        model_name=model_name,
        device=device,
    )
    return client.get_collection(
        name=collection_name,
        embedding_function=embedding_function,
    )
