from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agent.ontology_canonicalization import apply_healthy_genotype_disease_normalization
from agent.state import PipelineState
from validator.ontology_validator import ground_all_fields
import validator.grounders.disease as disease_grounder


def _genotype_match(raw: str) -> dict:
    return {
        "status": "FALLBACK",
        "score": None,
        "match_type": "fallback",
        "matched_label": None,
        "matched_term_id": None,
        "matched_source": None,
        "raw_value": raw,
        "matched_via": "healthy_genotype_normalized",
    }


def _base_output(**overrides: str) -> dict:
    base = {
        "gse_accession": "GSE000111",
        "gsm_accession": "GSM000222",
        "data_type": "RNA-seq",
        "organism": "Mus musculus",
        "tissue_type": "Liver",
        "cell_line": "No",
        "disease": "Healthy, Ldlr-/- Leiden mice",
        "treatment": "None",
    }
    base.update(overrides)
    return base


def test_healthy_genotype_disease_normalization_applies() -> None:
    state = PipelineState(
        gsm_accession="GSM000222",
        gse_accession="GSE000111",
        final_output=_base_output(),
        ontology_matches={"disease": _genotype_match("Healthy, Ldlr-/- Leiden mice")},
        semantic_errors={"disease": ["disease_inferred_without_evidence"]},
    )

    apply_healthy_genotype_disease_normalization(state, {})

    assert state.final_output["disease"] == "Healthy"
    assert "disease_contains_genotype_context" in state.flags
    assert "disease" not in state.semantic_errors
    assert state.locked_fields["disease"]["label"] == "Healthy"


def test_healthy_genotype_disease_detection_skips_grounder(monkeypatch) -> None:
    def _raise(*_args, **_kwargs):
        raise AssertionError("ground_disease should not be called")

    monkeypatch.setattr(disease_grounder, "ground_disease", _raise, raising=False)

    llm_output = {
        "organism": "Mus musculus",
        "disease": "Healthy, Ldlr-/- Leiden mice",
        "tissue_type": "Liver",
        "cell_line": "No",
        "data_type": "RNA-seq",
    }

    matches, failures = ground_all_fields(llm_output, "", {})

    assert "disease" not in failures
    assert matches["disease"].status == "FALLBACK"
    assert matches["disease"].matched_via == "healthy_genotype_normalized"


def test_healthy_genotype_disease_normalization_skips_disease_terms() -> None:
    state = PipelineState(
        gsm_accession="GSM000223",
        gse_accession="GSE000111",
        final_output=_base_output(disease="Healthy tissue adjacent to tumor"),
        ontology_matches={"disease": {"matched_via": "label_norm"}},
    )

    apply_healthy_genotype_disease_normalization(state, {})

    assert state.final_output["disease"] == "Healthy tissue adjacent to tumor"
    assert "disease_contains_genotype_context" not in state.flags
