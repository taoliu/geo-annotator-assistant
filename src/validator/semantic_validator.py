from __future__ import annotations
from typing import Dict, List
import re

# Failure codes
TISSUE_IS_CELL_TYPE = "tissue_is_cell_type"
TREATMENT_IDENTITY_LEAKAGE = "treatment_identity_leakage"
CELL_LINE_YES_INVALID = "cell_line_yes_invalid"
DISEASE_INFERRED_WITHOUT_EVIDENCE = "disease_inferred_without_evidence"

_CELL_WORD_RE = re.compile(r"\bcell(s)?\b", re.IGNORECASE)
_TISSUE_CELL_SUFFIXES = ("cells", "cell", "lymphocyte", "neuron", "macrophage")
_GENOTYPE_RE = re.compile(r"\b(ko|knockout|transgenic|cre)\b", re.IGNORECASE)
_GENOTYPE_SYMBOL_RE = re.compile(r"(\+\/\+|\+\/-|-\/-)")
_TREATMENT_TISSUE_WORDS_RE = re.compile(r"\b(liver|brain|blood|intestine)\b", re.IGNORECASE)

def semantic_validate(parsed_output: Dict[str, str], context_text: str) -> Dict[str, List[str]]:
    """Lightweight field-level semantic validation (no ontology calls)."""
    errs: Dict[str, List[str]] = {}

    tissue = parsed_output.get("tissue_type", "")
    if tissue and tissue != "Unknown":
        tissue_lower = tissue.strip().lower()
        if _CELL_WORD_RE.search(tissue) or tissue_lower.endswith(_TISSUE_CELL_SUFFIXES):
            errs.setdefault("tissue_type", []).append(TISSUE_IS_CELL_TYPE)

    treatment = parsed_output.get("treatment", "")
    if treatment and treatment != "None":
        if (
            _CELL_WORD_RE.search(treatment)
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
        cues = [
            "disease",
            "tumor",
            "cancer",
            "carcinoma",
            "leukemia",
            "lymphoma",
            "infection",
            "patient",
            "diagnos",
        ]
        if not any(c in context_text.lower() for c in cues):
            errs.setdefault("disease", []).append(DISEASE_INFERRED_WITHOUT_EVIDENCE)

    return errs
