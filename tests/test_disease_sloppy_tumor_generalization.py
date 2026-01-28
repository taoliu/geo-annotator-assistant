from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agent.ontology_canonicalization import apply_sloppy_tumor_disease_generalization
from agent.state import PipelineState


def _tissue_match(label: str, *, status: str = "MATCHED") -> dict:
    return {
        "status": status,
        "score": 1.0 if status == "MATCHED" else 0.6,
        "match_type": "label_norm_exact" if status == "MATCHED" else "jaccard",
        "matched_label": label,
        "matched_term_id": "UBERON:0002048",
        "matched_source": "Uberon Ontology",
    }


def _disease_match(raw: str, query: str) -> dict:
    return {
        "status": "MATCHED",
        "score": 1.0,
        "match_type": "label_norm_exact",
        "matched_label": query,
        "matched_term_id": "DOID:1324",
        "matched_source": "Human Disease Ontology",
        "raw_value": raw,
        "query_used": query,
    }


def _base_output(**overrides: str) -> dict:
    base = {
        "gse_accession": "GSE000111",
        "gsm_accession": "GSM000222",
        "data_type": "RNA-seq",
        "organism": "Homo sapiens",
        "tissue_type": "Lung",
        "cell_line": "No",
        "disease": "Lung Tumor",
        "treatment": "None",
    }
    base.update(overrides)
    return base


def test_sloppy_tumor_generalization_applies_and_locks() -> None:
    state = PipelineState(
        gsm_accession="GSM000222",
        gse_accession="GSE000111",
        final_output=_base_output(),
        ontology_matches={
            "tissue_type": _tissue_match("lung"),
            "disease": _disease_match("Lung Tumor", "lung cancer"),
        },
    )

    apply_sloppy_tumor_disease_generalization(state, {})

    assert state.final_output["disease"] == "lung cancer"
    assert "disease_generalized_from_sloppy_tumor_label" in state.flags
    assert state.locked_fields["disease"]["label"] == "lung cancer"


def test_sloppy_tumor_generalization_skips_non_human() -> None:
    state = PipelineState(
        gsm_accession="GSM000223",
        gse_accession="GSE000111",
        final_output=_base_output(organism="Mus musculus"),
        ontology_matches={
            "tissue_type": _tissue_match("lung"),
            "disease": _disease_match("Lung Tumor", "lung cancer"),
        },
    )

    apply_sloppy_tumor_disease_generalization(state, {})

    assert state.final_output["disease"] == "Lung Tumor"
    assert "disease_generalized_from_sloppy_tumor_label" not in state.flags


def test_sloppy_tumor_generalization_skips_model_identifier() -> None:
    state = PipelineState(
        gsm_accession="GSM000224",
        gse_accession="GSE000111",
        final_output=_base_output(disease="CT26 lung tumor"),
        ontology_matches={
            "tissue_type": _tissue_match("lung"),
            "disease": _disease_match("CT26 lung tumor", "lung cancer"),
        },
    )

    apply_sloppy_tumor_disease_generalization(state, {})

    assert state.final_output["disease"] == "CT26 lung tumor"
    assert "disease_generalized_from_sloppy_tumor_label" not in state.flags


def test_sloppy_tumor_generalization_requires_terminal_tissue_match() -> None:
    state = PipelineState(
        gsm_accession="GSM000225",
        gse_accession="GSE000111",
        final_output=_base_output(),
        ontology_matches={
            "tissue_type": _tissue_match("lung", status="LOW_CONFIDENCE"),
            "disease": _disease_match("Lung Tumor", "lung cancer"),
        },
    )

    apply_sloppy_tumor_disease_generalization(state, {})

    assert state.final_output["disease"] == "Lung Tumor"
    assert "disease_generalized_from_sloppy_tumor_label" not in state.flags
