from __future__ import annotations

import re

_NORMALIZE_RE = re.compile(r"[^a-z0-9]+")

_NON_ANSWER_PLACEHOLDERS = {
    "unknown",
    "not sure",
    "not clear",
    "unclear",
    "n a",
    "na",
    "none",
    "not provided",
    "?",
}


def normalize_non_answer(value: str) -> str:
    text = (value or "").strip().lower()
    if not text:
        return ""
    if text == "?":
        return "?"
    normalized = _NORMALIZE_RE.sub(" ", text).strip()
    return " ".join(normalized.split())


def is_llm_non_answer_placeholder(value: str) -> bool:
    normalized = normalize_non_answer(value)
    if not normalized:
        return False
    return normalized in _NON_ANSWER_PLACEHOLDERS
