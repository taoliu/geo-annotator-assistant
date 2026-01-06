from __future__ import annotations
from typing import Dict, List
import re

from validator.failure_codes import (
    CELL_LINE_INFERRED_WITHOUT_EVIDENCE,
    CELL_LINE_IS_CELL_TYPE,
    CELL_LINE_YES_INVALID,
    DISEASE_INFERRED_WITHOUT_EVIDENCE,
    TISSUE_TYPE_IS_CELL_TYPE,
    TREATMENT_IDENTITY_LEAKAGE,
)
from validator.cell_line_rules import is_cell_line_cell_type, is_cell_type_like
from validator.heuristics import get_heuristics

_HEURISTICS = get_heuristics()
_SEMANTIC = _HEURISTICS["semantic"]


def _compile_word_regex(words: List[str]) -> re.Pattern:
    escaped = [re.escape(word) for word in words]
    return re.compile(r"\b(?:%s)\b" % "|".join(escaped), re.IGNORECASE)


def _compile_symbol_regex(symbols: List[str]) -> re.Pattern:
    escaped = [re.escape(symbol) for symbol in symbols]
    return re.compile(r"(?:%s)" % "|".join(escaped))


_TISSUE_CELL_WORD_RE = _compile_word_regex(_SEMANTIC["tissue_cell_keywords"])
_TREATMENT_IDENTITY_WORD_RE = _compile_word_regex(
    _SEMANTIC["treatment_identity_keywords"]
)
_TISSUE_CELL_SUFFIXES = tuple(_SEMANTIC["tissue_cell_suffixes"])

_GENOTYPE_KEYWORDS = _SEMANTIC["treatment_genotype_keywords"]
_GENOTYPE_SYMBOLS = [kw for kw in _GENOTYPE_KEYWORDS if any(ch in kw for ch in "+-/")]
_GENOTYPE_WORDS = [kw for kw in _GENOTYPE_KEYWORDS if kw not in _GENOTYPE_SYMBOLS]

_GENOTYPE_RE = _compile_word_regex(_GENOTYPE_WORDS)
_GENOTYPE_SYMBOL_RE = _compile_symbol_regex(_GENOTYPE_SYMBOLS)
_TREATMENT_TISSUE_WORDS_RE = _compile_word_regex(_SEMANTIC["treatment_tissue_keywords"])

_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")


def _normalize_for_evidence(text: str) -> str:
    return _NON_ALNUM_RE.sub("", text.lower())


def _has_explicit_value(value: str, context_text: str) -> bool:
    if not value or not context_text:
        return False
    value = value.strip()
    if not value:
        return False
    if re.search(r"\b%s\b" % re.escape(value), context_text, re.IGNORECASE):
        return True
    normalized_value = _normalize_for_evidence(value)
    if len(normalized_value) < 4:
        return False
    normalized_context = _normalize_for_evidence(context_text)
    return normalized_value in normalized_context


def semantic_validate(parsed_output: Dict[str, str], context_text: str) -> Dict[str, List[str]]:
    """Lightweight field-level semantic validation (no ontology calls)."""
    errs: Dict[str, List[str]] = {}

    tissue_value = (parsed_output.get("tissue_type") or "").strip()
    if tissue_value and tissue_value.lower() not in {"unknown", "no"}:
        tissue_lower = tissue_value.lower()
        if (
            _TISSUE_CELL_WORD_RE.search(tissue_value)
            or tissue_lower.endswith(_TISSUE_CELL_SUFFIXES)
            or is_cell_type_like(tissue_value)
        ):
            errs.setdefault("tissue_type", []).append(TISSUE_TYPE_IS_CELL_TYPE)

    treatment = parsed_output.get("treatment", "")
    if treatment and treatment != "None":
        if (
            _TREATMENT_IDENTITY_WORD_RE.search(treatment)
            or _GENOTYPE_RE.search(treatment)
            or _GENOTYPE_SYMBOL_RE.search(treatment)
            or _TREATMENT_TISSUE_WORDS_RE.search(treatment)
        ):
            errs.setdefault("treatment", []).append(TREATMENT_IDENTITY_LEAKAGE)

    cell_line = parsed_output.get("cell_line", "")
    cell_line_value = cell_line.strip()
    cell_line_lower = cell_line_value.lower()
    if cell_line_value and cell_line_lower == "yes":
        errs.setdefault("cell_line", []).append(CELL_LINE_YES_INVALID)
    elif cell_line_value and cell_line_lower not in {"no", "unknown"}:
        if is_cell_line_cell_type(cell_line_value):
            errs.setdefault("cell_line", []).append(CELL_LINE_IS_CELL_TYPE)
        elif not _has_explicit_value(cell_line_value, context_text):
            errs.setdefault("cell_line", []).append(CELL_LINE_INFERRED_WITHOUT_EVIDENCE)

    disease = parsed_output.get("disease", "")
    if disease and disease != "Healthy":
        # Very conservative: if context has no common disease cues, flag.
        cues = _SEMANTIC["disease_cues"]
        if not any(c in context_text.lower() for c in cues):
            errs.setdefault("disease", []).append(DISEASE_INFERRED_WITHOUT_EVIDENCE)

    return errs
