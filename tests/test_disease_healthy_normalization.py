from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agent.ontology_canonicalization import apply_healthy_control_disease_normalization
from agent.state import PipelineState


def _healthy_match(raw: str) -> dict:
    return {
        "status": "FALLBACK",
        "score": None,
        "match_type": "fallback",
        "matched_label": None,
        "matched_term_id": None,
        "matched_source": None,
        "raw_value": raw,
        "matched_via": "healthy_control_normalized",
    }


def _base_output(**overrides: str) -> dict:
    base = {
        "gse_accession": "GSE000111",
        "gsm_accession": "GSM000222",
        "data_type": "RNA-seq",
        "organism": "Homo sapiens",
        "tissue_type": "Blood",
        "cell_line": "No",
        "disease": "Healthy Donors",
        "treatment": "None",
    }
    base.update(overrides)
    return base


def test_healthy_control_disease_normalization_applies() -> None:
    state = PipelineState(
        gsm_accession="GSM000222",
        gse_accession="GSE000111",
        final_output=_base_output(),
        ontology_matches={"disease": _healthy_match("Healthy Donors")},
        semantic_errors={"disease": ["disease_inferred_without_evidence"]},
    )

    apply_healthy_control_disease_normalization(state, {})

    assert state.final_output["disease"] == "Healthy"
    assert "disease_normalized_to_healthy" in state.flags
    assert "disease" not in state.semantic_errors
    assert state.locked_fields["disease"]["label"] == "Healthy"


def test_healthy_control_disease_normalization_skips_unmatched() -> None:
    state = PipelineState(
        gsm_accession="GSM000223",
        gse_accession="GSE000111",
        final_output=_base_output(disease="tumor control arm"),
        ontology_matches={"disease": {"matched_via": "label_norm"}},
    )

    apply_healthy_control_disease_normalization(state, {})

    assert state.final_output["disease"] == "tumor control arm"
    assert "disease_normalized_to_healthy" not in state.flags
