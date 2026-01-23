from __future__ import annotations

from dataclasses import dataclass
import json
import os
import re
from typing import List, Optional, Sequence

from rag.chroma_client import build_embedding_function, get_chroma_collection


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
    retrieval_mode: Optional[str] = None
    query_candidate: Optional[str] = None


_WS_RE = re.compile(r"\s+")
_QUOTED_RE = re.compile(r"\"([^\"]+)\"|'([^']+)'")
_ID_TOKEN_RE = re.compile(r"\b[A-Z]{2,10}:[A-Za-z0-9._-]+\b")
_HYPHEN_TOKEN_RE = re.compile(r"\b[A-Za-z0-9]+(?:[-_][A-Za-z0-9]+)+\b")
_KEEP_CHARS_RE = re.compile(r"[^a-z0-9-]+")
_MULTI_DASH_RE = re.compile(r"-{2,}")

_SOURCE_FIELD_MAP = {
    "Cellosaurus": "cell_line",
    "Cell Ontology": "cell_type",
    "Uberon Ontology": "tissue_type",
    "Human Disease Ontology": "disease",
    "Experimental Factor Ontology": "data_type",
    "NCI Thesaurus": "cancer_type",
}


def extract_candidates(query: str) -> List[str]:
    text = query or ""
    candidates: List[str] = []
    seen = set()

    def _add(value: Optional[str]) -> None:
        if not value:
            return
        cleaned = value.strip()
        if not cleaned or cleaned in seen:
            return
        seen.add(cleaned)
        candidates.append(cleaned)

    for match in _QUOTED_RE.finditer(text):
        _add(match.group(1) or match.group(2))

    for token in _ID_TOKEN_RE.findall(text):
        _add(token)

    for token in _HYPHEN_TOKEN_RE.findall(text):
        _add(token)

    stripped = text.strip()
    if stripped and len(stripped) < 64:
        _add(stripped)

    return candidates


def normalize_exact_variants(value: str) -> dict[str, str]:
    cleaned = (value or "").strip().lower()
    cleaned = cleaned.replace("_", "-")
    cleaned = _WS_RE.sub("-", cleaned)
    cleaned = _KEEP_CHARS_RE.sub("", cleaned)
    cleaned = _MULTI_DASH_RE.sub("-", cleaned)
    cleaned = cleaned.strip("-")
    return {
        "hyphen": cleaned,
        "compact": cleaned.replace("-", ""),
        "space": cleaned.replace("-", " "),
    }


def _coerce_synonyms(value) -> List[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if item is not None and str(item).strip()]
    if isinstance(value, (tuple, set)):
        return [str(item).strip() for item in value if item is not None and str(item).strip()]
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return []
        if s.startswith("[") and s.endswith("]"):
            try:
                parsed = json.loads(s)
            except json.JSONDecodeError:
                parsed = None
            if isinstance(parsed, list):
                return [
                    str(item).strip()
                    for item in parsed
                    if item is not None and str(item).strip()
                ]
            if isinstance(parsed, str):
                parsed_value = parsed.strip()
                return [parsed_value] if parsed_value else []
        if "," in s:
            parts = [p.strip() for p in s.split(",")]
            return [p for p in parts if p]
        return [s]
    return []


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
    retrieval_mode: Optional[str] = None,
    query_candidate: Optional[str] = None,
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
        retrieval_mode=retrieval_mode,
        query_candidate=query_candidate,
    )


def _extract_get_results(result) -> tuple[List, List, List]:
    if not isinstance(result, dict):
        return [], [], []
    ids = _maybe_flatten(_ensure_list(result.get("ids")))
    metas = _maybe_flatten(_ensure_list(result.get("metadatas")))
    docs = _maybe_flatten(_ensure_list(result.get("documents")))
    return ids, metas, docs


def _collection_get(
    collection,
    *,
    ids=None,
    where=None,
    include=None,
    limit=None,
):
    kwargs = {}
    if ids is not None:
        kwargs["ids"] = ids
    if where is not None:
        kwargs["where"] = where
    if include is not None:
        kwargs["include"] = include
    if limit is not None:
        kwargs["limit"] = limit
    try:
        return collection.get(**kwargs)
    except TypeError:
        kwargs.pop("include", None)
        kwargs.pop("limit", None)
        try:
            return collection.get(**kwargs)
        except Exception:
            return None
    except Exception:
        return None


def _filter_candidates_by_source(
    candidates: List[OntologyCandidate],
    source: Optional[str],
) -> List[OntologyCandidate]:
    if not candidates or not source:
        return candidates
    return [candidate for candidate in candidates if candidate.source == source]


def _sort_candidates_by_term_id(
    candidates: List[OntologyCandidate],
) -> List[OntologyCandidate]:
    return sorted(candidates, key=lambda candidate: candidate.term_id or "")


def _build_meta_exact_where(
    variants: dict[str, str],
    source: Optional[str],
) -> Optional[dict]:
    clauses: List[dict] = []

    def _add_clause(key: str, value: str) -> None:
        if value:
            clauses.append({key: value})

    _add_clause("label_norm", variants.get("hyphen", ""))
    _add_clause("label_norm_compact", variants.get("compact", ""))
    _add_clause("label_norm_space", variants.get("space", ""))

    source_field = _SOURCE_FIELD_MAP.get(source or "")
    if source_field:
        _add_clause(source_field, variants.get("hyphen", ""))
        _add_clause(f"{source_field}_compact", variants.get("compact", ""))
        _add_clause(f"{source_field}_space", variants.get("space", ""))

    if not clauses:
        return None

    or_clause = {"$or": clauses}
    if source:
        return {"$and": [{"source": source}, or_clause]}
    return or_clause


def _build_candidates_from_get(
    result,
    source: Optional[str],
    distance: Optional[float],
    retrieval_mode: str,
    query_candidate: str,
) -> List[OntologyCandidate]:
    ids, metas, docs = _extract_get_results(result)
    candidates: List[OntologyCandidate] = []
    for term_id, meta, doc in zip(ids, metas, docs):
        candidates.append(
            _build_candidate(
                term_id,
                distance,
                meta,
                doc,
                source or "",
                retrieval_mode=retrieval_mode,
                query_candidate=query_candidate,
            )
        )
    return _filter_candidates_by_source(candidates, source)


def retrieve_ontology_candidates(
    query: str,
    source: str,
    persist_path: str,
    collection_name: str,
    embedding_model_name: str,
    normalize_embeddings: bool,
    embedding_device: str = "cpu",
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

    del normalize_embeddings

    try:
        collection = get_chroma_collection(
            persist_path,
            collection_name,
        )
    except Exception as exc:
        raise OntologyIndexUnavailable(
            f"Chroma collection not available: {collection_name!r}"
        ) from exc

    candidates = extract_candidates(query)
    for candidate in candidates:
        if _ID_TOKEN_RE.fullmatch(candidate):
            id_result = _collection_get(
                collection,
                ids=[candidate],
                include=["metadatas", "documents"],
            )
            id_candidates = _build_candidates_from_get(
                id_result,
                source,
                0.0,
                retrieval_mode="id_get",
                query_candidate=candidate,
            )
            if id_candidates:
                return _sort_candidates_by_term_id(id_candidates)[:top_k]

        variants = normalize_exact_variants(candidate)
        where = _build_meta_exact_where(variants, source)
        if where:
            meta_result = _collection_get(
                collection,
                where=where,
                include=["metadatas", "documents"],
                limit=top_k,
            )
            meta_candidates = _build_candidates_from_get(
                meta_result,
                source,
                0.0,
                retrieval_mode="meta_exact",
                query_candidate=candidate,
            )
            if meta_candidates:
                return _sort_candidates_by_term_id(meta_candidates)[:top_k]

    where = {"source": source} if source else None
    embedding_function = build_embedding_function(
        model_name=embedding_model_name,
        device=embedding_device,
    )
    query_embeddings = embedding_function([query])
    try:
        res = collection.query(
            query_embeddings=query_embeddings,
            n_results=top_k,
            where=where,
            include=["metadatas", "documents", "distances"],
        )
    except TypeError:
        try:
            res = collection.query(
                query_embeddings=query_embeddings,
                n_results=top_k,
                where=where,
            )
        except Exception as exc:
            raise OntologyIndexUnavailable("Chroma query failed.") from exc
    except Exception as exc:
        raise OntologyIndexUnavailable("Chroma query failed.") from exc

    ids = (res.get("ids") or [[]])[0]
    dists = (res.get("distances") or [[]])[0]
    metas = (res.get("metadatas") or [[]])[0]
    docs = (res.get("documents") or [[]])[0]

    candidates_out: List[OntologyCandidate] = []
    for term_id, dist, meta, doc in zip(ids, dists, metas, docs):
        candidates_out.append(
            _build_candidate(
                term_id,
                dist,
                meta,
                doc,
                source,
                retrieval_mode="vector_fallback",
                query_candidate=query,
            )
        )

    return candidates_out
