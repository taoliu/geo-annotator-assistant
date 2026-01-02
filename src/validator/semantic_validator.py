from __future__ import annotations
from typing import Dict, List
import re

from validator.heuristics import get_heuristics

# Failure codes
TISSUE_IS_CELL_TYPE = "tissue_is_cell_type"
TREATMENT_IDENTITY_LEAKAGE = "treatment_identity_leakage"
CELL_LINE_YES_INVALID = "cell_line_yes_invalid"
DISEASE_INFERRED_WITHOUT_EVIDENCE = "disease_inferred_without_evidence"

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

def semantic_validate(parsed_output: Dict[str, str], context_text: str) -> Dict[str, List[str]]:
    """Lightweight field-level semantic validation (no ontology calls)."""
    errs: Dict[str, List[str]] = {}

    tissue = parsed_output.get("tissue_type", "")
    if tissue and tissue != "Unknown":
        tissue_lower = tissue.strip().lower()
        if _TISSUE_CELL_WORD_RE.search(tissue) or tissue_lower.endswith(_TISSUE_CELL_SUFFIXES):
            errs.setdefault("tissue_type", []).append(TISSUE_IS_CELL_TYPE)

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
    if cell_line and cell_line.strip().lower() == "yes":
        errs.setdefault("cell_line", []).append(CELL_LINE_YES_INVALID)

    disease = parsed_output.get("disease", "")
    if disease and disease != "Healthy":
        # Very conservative: if context has no common disease cues, flag.
        cues = _SEMANTIC["disease_cues"]
        if not any(c in context_text.lower() for c in cues):
            errs.setdefault("disease", []).append(DISEASE_INFERRED_WITHOUT_EVIDENCE)

    return errs
