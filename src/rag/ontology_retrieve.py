from __future__ import annotations

from dataclasses import dataclass
import traceback
from typing import List, Optional, Sequence
import os

from rag.chroma_client import get_chroma_client


class OntologyIndexUnavailable(RuntimeError):
    """Raised when the ontology Chroma index cannot be accessed."""


@dataclass(frozen=True)
class OntologyCandidate:
    term_id: str
    label: str
    source: str
    definition: Optional[str]
    synonyms: List[str]
    ancestors: List[dict]
    distance: Optional[float]
    doc_text: Optional[str] = None


def _load_embedding_function(model_name: str, normalize_embeddings: bool):
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
    except ImportError as exc:
        raise RuntimeError(
            "HuggingFaceEmbeddings is not available. Install langchain-huggingface."
        ) from exc

    try:
        return HuggingFaceEmbeddings(
            model_name=model_name,
            encode_kwargs={"normalize_embeddings": normalize_embeddings},
        )
    except Exception as exc:
        raise RuntimeError(
            f"Failed to initialize embeddings for model {model_name!r}."
        ) from exc


def _coerce_synonyms(value) -> List[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if item is not None and str(item).strip()]
    if isinstance(value, (tuple, set)):
        return [str(item).strip() for item in value if item is not None and str(item).strip()]
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return []
        # Handle the observed "one big comma-separated string" case.
        if "," in s:
            parts = [p.strip() for p in s.split(",")]
            return [p for p in parts if p]
        return [s]
    return []


def _canonicalize_label_for_lookup(label: str) -> str:
    cleaned = " ".join((label or "").strip().split())
    if not cleaned:
        return ""
    lowered = cleaned.lower()
    if lowered in {"atac seq", "atacseq", "atac-seq"}:
        return "ATAC-seq"
    return cleaned


def _ensure_list(value) -> List:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return []


def _maybe_flatten(value: Sequence) -> List:
    if not value:
        return []
    if isinstance(value, list) and len(value) == 1 and isinstance(value[0], list):
        return value[0]
    return list(value)



def _build_candidate(
    term_id,
    dist,
    meta,
    doc,
    source: str,
) -> OntologyCandidate:
    meta = meta if isinstance(meta, dict) else {}
    term_id_value = meta.get("term_id") or term_id
    label = meta.get("label") or ""
    definition = meta.get("definition") or None
    synonyms = _coerce_synonyms(meta.get("synonyms", []))
    ancestors = meta.get("ancestors")
    source_value = meta.get("source") or source
    return OntologyCandidate(
        term_id=str(term_id_value or ""),
        label=str(label or ""),
        source=str(source_value or ""),
        definition=str(definition) if definition else None,
        synonyms=synonyms,
        ancestors=ancestors if isinstance(ancestors, list) else [],
        distance=float(dist) if dist is not None else None,
        doc_text=str(doc) if doc else None,
    )


def retrieve_ontology_candidates(
    query: str,
    source: str,
    persist_path: str,
    collection_name: str,
    embedding_model_name: str,
    normalize_embeddings: bool,
    top_k: int = 20,
) -> List[OntologyCandidate]:
    query = (query or "").strip()
    if not query:
        return []
    if not source:
        raise ValueError("Ontology source is required for retrieval.")
    if not collection_name:
        raise OntologyIndexUnavailable("Ontology collection name is required.")
    if not persist_path or not os.path.isdir(persist_path):
        raise OntologyIndexUnavailable(
            f"Chroma persist_path not found: {persist_path!r}"
        )
    sqlite_path = os.path.join(persist_path, "chroma.sqlite3")
    if not os.path.isfile(sqlite_path):
        raise OntologyIndexUnavailable(
            f"Chroma sqlite file not found: {sqlite_path!r}"
        )

    embedding_function = _load_embedding_function(
        embedding_model_name,
        normalize_embeddings,
    )
    try:
        client = get_chroma_client(persist_path)
    except Exception as exc:
        raise OntologyIndexUnavailable("Failed to open Chroma client.") from exc
    try:
        collection = client.get_collection(name=collection_name)
    except Exception as exc:
        raise OntologyIndexUnavailable(
            f"Chroma collection not available: {collection_name!r}"
        ) from exc

    query_embedding = embedding_function.embed_query(query)
    try:
        res = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where={"source": source},
            include=["metadatas", "documents", "distances"],
        )
    except TypeError:
        try:
            res = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where={"source": source},
            )
        except Exception as exc:
            raise OntologyIndexUnavailable("Chroma query failed.") from exc
    except Exception as exc:
        raise OntologyIndexUnavailable("Chroma query failed.") from exc

    ids = (res.get("ids") or [[]])[0]
    dists = (res.get("distances") or [[]])[0]
    metas = (res.get("metadatas") or [[]])[0]
    docs = (res.get("documents") or [[]])[0]

    candidates: List[OntologyCandidate] = []
    for term_id, dist, meta, doc in zip(ids, dists, metas, docs):
        candidates.append(_build_candidate(term_id, dist, meta, doc, source))

    canonical_label = _canonicalize_label_for_lookup(query)
    if canonical_label:
        exact_res = None

        # 1) Try simple where (matches your test)
        try:
            exact_res = collection.get(
                where={"source": source, "label": canonical_label},
                include=["metadatas", "documents"],
            )
        except Exception:
            exact_res = None
        # 2) If needed, try $and form (keeps your previous compatibility)
        if not exact_res:
            try:
                exact_res = collection.get(
                    where={"$and": [{"source": source}, {"label": canonical_label}]},
                    include=["metadatas", "documents"],
                )
            except Exception:
                exact_res = None

        if exact_res:
            exact_ids = _maybe_flatten(_ensure_list(exact_res.get("ids")))
            exact_metas = _maybe_flatten(_ensure_list(exact_res.get("metadatas")))
            exact_docs = _maybe_flatten(_ensure_list(exact_res.get("documents")))
            exact_candidates: List[OntologyCandidate] = []
            for term_id, meta, doc in zip(exact_ids, exact_metas, exact_docs):
                exact_candidates.append(
                    _build_candidate(term_id, None, meta, doc, source)
                )
            if exact_candidates:
                seen = {candidate.term_id for candidate in candidates}
                prepended: List[OntologyCandidate] = []
                for candidate in exact_candidates:
                    if candidate.term_id and candidate.term_id not in seen:
                        prepended.append(candidate)
                        seen.add(candidate.term_id)
                candidates = prepended + candidates

    return candidates
