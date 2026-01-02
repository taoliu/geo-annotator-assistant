from __future__ import annotations
from typing import Dict, List

ASSAY_PLATFORM_CONFLICT = "assay_platform_conflict"
SINGLE_CELL_EVIDENCE_MISSING = "single_cell_evidence_missing"
HEALTHY_DISEASE_CONFLICT = "healthy_disease_conflict"
ORGANISM_CONTEXT_CONFLICT = "organism_context_conflict"

def consistency_validate(parsed_output: Dict[str, str], context_text: str) -> List[str]:
    """Keyword-based cross-field consistency checks."""
    flags: List[str] = []
    ctx = context_text.lower()

    dt = parsed_output.get("data_type", "").lower()
    if dt in {"scrna-seq", "snrna-seq", "scatac-seq", "snatac-seq"}:
        sc_kw = ["single cell", "single-cell", "single nucleus", "single-nucleus", "10x", "smart-seq", "drop-seq", "chromium"]
        if not any(k in ctx for k in sc_kw):
            flags.append(SINGLE_CELL_EVIDENCE_MISSING)

    if dt == "microarray":
        seq_kw = ["illumina novaseq", "nextseq", "hiseq", "miseq", "sequencing", "rna-seq", "atac-seq", "chip-seq"]
        if any(k in ctx for k in seq_kw):
            flags.append(ASSAY_PLATFORM_CONFLICT)

    disease = parsed_output.get("disease", "")
    if disease == "Healthy":
        disease_kw = ["tumor", "cancer", "carcinoma", "leukemia", "lymphoma", "disease:", "infect"]
        if any(k in ctx for k in disease_kw):
            flags.append(HEALTHY_DISEASE_CONFLICT)

    org = parsed_output.get("organism", "").lower()
    if org:
        # simple check for common mismatches
        if "mus musculus" in org and "homo sapiens" in ctx:
            flags.append(ORGANISM_CONTEXT_CONFLICT)
        if "homo sapiens" in org and "mus musculus" in ctx:
            flags.append(ORGANISM_CONTEXT_CONFLICT)

    return sorted(set(flags))
