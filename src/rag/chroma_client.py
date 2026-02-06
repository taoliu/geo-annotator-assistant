from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
from threading import RLock
from typing import Any

from agent.runtime_trace import (
    log_chroma_client_initialized,
    log_chroma_collection_opened,
)


@dataclass
class _ChromaClientEntry:
    client: Any
    collections: dict[str, Any] = field(default_factory=dict)


_CACHE_LOCK = RLock()
_CLIENT_CACHE: dict[tuple[str, str], _ChromaClientEntry] = {}


def _settings_cache_key(settings: Any | None) -> str:
    if settings is None:
        return ""
    try:
        return json.dumps(
            settings,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            default=str,
        )
    except Exception:
        return repr(settings)


def _build_client_cache_key(
    persist_path: str,
    client_settings: Any | None,
) -> tuple[str, str]:
    return (os.path.abspath(persist_path), _settings_cache_key(client_settings))


def _get_or_create_client_entry(
    persist_path: str,
    client_settings: Any | None = None,
) -> tuple[tuple[str, str], _ChromaClientEntry]:
    if not persist_path or not os.path.isdir(persist_path):
        raise ValueError(f"Chroma persist_path not found: {persist_path!r}")

    cache_key = _build_client_cache_key(persist_path, client_settings)
    with _CACHE_LOCK:
        entry = _CLIENT_CACHE.get(cache_key)
        if entry is not None:
            return cache_key, entry

        # Lazy import so other modules can import without chromadb installed in some contexts.
        import chromadb

        client_kwargs: dict[str, Any] = {"path": persist_path}
        if client_settings is not None:
            client_kwargs["settings"] = client_settings
        client = chromadb.PersistentClient(**client_kwargs)
        entry = _ChromaClientEntry(client=client)
        _CLIENT_CACHE[cache_key] = entry
        log_chroma_client_initialized(persist_path)
        return cache_key, entry


def reset_chroma_client_cache() -> None:
    """Clear in-process cached Chroma clients/collections (tests only)."""
    with _CACHE_LOCK:
        _CLIENT_CACHE.clear()


def get_chroma_client(
    persist_path: str,
    client_settings: Any | None = None,
) -> Any:
    """Get a cached ChromaDB client for a local persist directory."""
    _, entry = _get_or_create_client_entry(
        persist_path=persist_path,
        client_settings=client_settings,
    )
    return entry.client


def _get_cached_collection(
    *,
    persist_path: str,
    collection_name: str,
    client_settings: Any | None,
    collection_method: str,
    collection_kwargs: dict[str, Any] | None = None,
) -> Any:
    if not collection_name:
        raise ValueError("Chroma collection_name is required.")

    cache_key, entry = _get_or_create_client_entry(
        persist_path=persist_path,
        client_settings=client_settings,
    )

    del cache_key
    with _CACHE_LOCK:
        cached = entry.collections.get(collection_name)
        if cached is not None:
            return cached

        kwargs = dict(collection_kwargs or {})
        if collection_method == "get":
            collection = entry.client.get_collection(name=collection_name, **kwargs)
        elif collection_method == "get_or_create":
            collection = entry.client.get_or_create_collection(
                name=collection_name,
                **kwargs,
            )
        else:
            raise ValueError(f"Unsupported collection_method: {collection_method!r}")
        entry.collections[collection_name] = collection
        log_chroma_collection_opened(collection_name)
        return collection


def get_chroma_collection(
    persist_path: str,
    collection_name: str,
    client_settings: Any | None = None,
    collection_kwargs: dict[str, Any] | None = None,
) -> Any:
    """Get a cached persisted Chroma collection handle."""
    return _get_cached_collection(
        persist_path=persist_path,
        collection_name=collection_name,
        client_settings=client_settings,
        collection_method="get",
        collection_kwargs=collection_kwargs,
    )


def get_or_create_chroma_collection(
    persist_path: str,
    collection_name: str,
    client_settings: Any | None = None,
    collection_kwargs: dict[str, Any] | None = None,
) -> Any:
    """Get or create a cached persisted Chroma collection handle."""
    return _get_cached_collection(
        persist_path=persist_path,
        collection_name=collection_name,
        client_settings=client_settings,
        collection_method="get_or_create",
        collection_kwargs=collection_kwargs,
    )


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
