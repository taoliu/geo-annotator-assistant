from __future__ import annotations

import re

_CELL_WORD_RE = re.compile(r"\bcell(s)?\b", re.IGNORECASE)
_IMMUNE_MARKER_RE = re.compile(
    r"\bcd3\b|\bcd4\b|\bcd8\b|\bb[- ]?cell(s)?\b|\bt[- ]?cell(s)?\b|\bnk\b",
    re.IGNORECASE,
)
_CELL_TYPE_RE = re.compile(r"\bpbmc\b|\bsplenocyte\b|\bthymocyte\b", re.IGNORECASE)
_CELL_QUALIFIER_RE = re.compile(r"\bprimary\b|\bsorted\b|\bfresh\b|ex vivo", re.IGNORECASE)


def _is_cell_type_like(value: str, include_qualifier: bool = True) -> bool:
    cleaned = (value or "").strip()
    if not cleaned:
        return False
    lowered = cleaned.lower()
    if lowered in {"no", "unknown"}:
        return False
    if _CELL_WORD_RE.search(cleaned):
        return True
    if _IMMUNE_MARKER_RE.search(cleaned):
        return True
    if _CELL_TYPE_RE.search(cleaned):
        return True
    if include_qualifier and _CELL_QUALIFIER_RE.search(cleaned):
        return True
    if "+" in cleaned and "cell" in lowered:
        return True
    return False


def is_cell_line_cell_type(value: str) -> bool:
    return _is_cell_type_like(value, include_qualifier=True)


def is_cell_type_like(value: str) -> bool:
    return _is_cell_type_like(value, include_qualifier=False)
