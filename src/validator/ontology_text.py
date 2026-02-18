from __future__ import annotations

import json
import re
from typing import Any, List, Sequence

_WS_RE = re.compile(r"\s+")
_EXACT_PUNCT_RE = re.compile(r"[-_/,.:]")
_NON_ALNUM_RE = re.compile(r"[^a-z0-9 ]+")


def normalize_exact_match_text(text: str) -> str:
    if not text:
        return ""
    normalized = text.strip().lower()
    normalized = _EXACT_PUNCT_RE.sub(" ", normalized)
    normalized = _NON_ALNUM_RE.sub(" ", normalized)
    normalized = _WS_RE.sub(" ", normalized).strip()
    return normalized


def coerce_synonyms(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return _clean_sequence(value)
    if isinstance(value, (tuple, set)):
        return _clean_sequence(list(value))
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return []
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            parsed = None
        if parsed is not None and parsed != value:
            return coerce_synonyms(parsed)
        if "," in stripped:
            return _clean_sequence([part.strip() for part in stripped.split(",")])
        return [stripped]
    return []


def normalize_synonyms(value: Any) -> List[str]:
    normalized: List[str] = []
    seen: set[str] = set()
    for synonym in coerce_synonyms(value):
        normalized_value = normalize_exact_match_text(synonym)
        if not normalized_value or normalized_value in seen:
            continue
        seen.add(normalized_value)
        normalized.append(normalized_value)
    return normalized


def synonym_pairs(value: Any) -> List[tuple[str, str]]:
    pairs: List[tuple[str, str]] = []
    for synonym in coerce_synonyms(value):
        normalized_value = normalize_exact_match_text(synonym)
        if not normalized_value:
            continue
        pairs.append((synonym, normalized_value))
    return pairs


def _clean_sequence(values: Sequence[Any]) -> List[str]:
    cleaned: List[str] = []
    seen: set[str] = set()
    for item in values:
        if item is None:
            continue
        text = str(item).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        cleaned.append(text)
    return cleaned
