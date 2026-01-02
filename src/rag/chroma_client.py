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
