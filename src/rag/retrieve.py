from __future__ import annotations
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timezone

from rag.candidate import OntologyCandidate
from rag.chroma_client import get_chroma_client

def retrieve_candidates(
    persist_path: str,
    collection_name: str,
    field: str,
    query_text: str,
    k: int = 10,
    filters: Optional[Dict[str, Any]] = None,
) -> Tuple[List[OntologyCandidate], Dict[str, Any]]:
    """Retrieve top-K ontology candidates from a Chroma collection.

    Returns (candidates, retrieval_meta).
    """
    query_text = (query_text or "").strip()
    if not query_text:
        return [], {"collection_name": collection_name, "k": k, "field": field, "ts": datetime.now(timezone.utc).isoformat()}

    client = get_chroma_client(persist_path)
    col = client.get_or_create_collection(name=collection_name)  # NOTE: read-only intent; should not add.
    res = col.query(query_texts=[query_text], n_results=k, where=filters or None, include=["metadatas", "distances", "documents", "ids"])
    ids = (res.get("ids") or [[]])[0]
    dists = (res.get("distances") or [[]])[0]
    metas = (res.get("metadatas") or [[]])[0]
    docs = (res.get("documents") or [[]])[0]

    cands: List[OntologyCandidate] = []
    for term_id, dist, meta, doc in zip(ids, dists, metas, docs):
        # Map distance -> score in [0,1]. If dist is cosine distance, score=1-dist.
        try:
            score = max(0.0, min(1.0, 1.0 - float(dist)))
        except Exception:
            score = 0.0
        preferred_label = ""
        synonyms = None
        ontology = meta.get("ontology") if isinstance(meta, dict) else None
        if isinstance(meta, dict):
            preferred_label = meta.get("preferred_label") or meta.get("label") or ""
            synonyms = meta.get("synonyms")
        if not preferred_label and isinstance(doc, str):
            preferred_label = doc
        cands.append(OntologyCandidate(
            ontology=str(ontology or ""),
            term_id=str(term_id),
            preferred_label=str(preferred_label),
            synonyms=synonyms if isinstance(synonyms, list) else None,
            score=score,
            metadata=meta if isinstance(meta, dict) else None,
        ))
    meta_out = {"collection_name": collection_name, "k": k, "field": field, "ts": datetime.now(timezone.utc).isoformat()}
    return cands, meta_out
