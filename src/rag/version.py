from __future__ import annotations
import hashlib
import os
from typing import Optional

def get_rag_version(persist_path: str, collection_name: str) -> str:
    """Return a stable version identifier for the local Chroma persist store.

    Fallback strategy: hash of (collection_name + persist_path + directory listing).
    """
    h = hashlib.sha1()
    h.update(collection_name.encode("utf-8"))
    h.update(b"|")
    h.update(os.path.abspath(persist_path).encode("utf-8"))
    try:
        entries = sorted(os.listdir(persist_path))
        for e in entries[:2000]:
            h.update(b"|")
            h.update(e.encode("utf-8"))
    except Exception:
        pass
    return h.hexdigest()
