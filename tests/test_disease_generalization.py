from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agent.ontology_canonicalization import apply_disease_modifier_generalization
from agent.repair_loop import apply_repairs
from agent.state import PipelineState
from validator.decision_engine import load_decision_table
from validator.failure_codes import ONTOLOGY_LOW_CONFIDENCE_DISEASE


def _decision_table() -> dict:
    return load_decision_table(str(ROOT / "spec" / "decision_table.yaml"))


def _full_output(*, disease: str) -> dict:
    return {
        "gse_accession": "GSE000",
        "gsm_accession": "GSM000",
        "data_type": "RNA-Seq",
        "organism": "Homo sapiens",
        "tissue_type": "Lung",
        "cell_line": "No",
        "disease": disease,
        "treatment": "None",
    }


def _low_confidence_match(raw_value: str, alternates: list[dict]) -> dict:
    return {
        "field": "disease",
        "raw_value": raw_value,
        "ontology": "Human Disease Ontology",
        "status": "LOW_CONFIDENCE",
        "matched_term_id": None,
        "matched_label": None,
        "matched_source": None,
        "match_type": "jaccard",
        "score": 0.55,
        "alternates": alternates,
    }


def test_disease_generalization_applies_and_skips_repairs() -> None:
    raw = "Kras-driven lung cancer"
    alternates = [
        {
            "term_id": "DOID:1324",
            "label": "lung cancer",
            "source": "Human Disease Ontology",
            "confidence": 0.55,
        }
    ]
    state = PipelineState(
        gsm_accession="GSM100",
        final_output=_full_output(disease=raw),
        ontology_matches={"disease": _low_confidence_match(raw, alternates)},
        ontology_failures={"disease": ONTOLOGY_LOW_CONFIDENCE_DISEASE},
    )

    apply_disease_modifier_generalization(state, {})

    assert state.final_output["disease"] == "lung cancer"
    assert state.ontology_failures.get("disease") is None
    assert state.locked_fields["disease"]["label"] == "lung cancer"
    assert "disease_generalized_for_ontology" in state.flags
    assert state.ontology_matches["disease"]["raw_value"] == raw

    class DummyLLM:
        def generate(self, request):
            raise AssertionError("Repair should not be triggered for generalized disease.")

    result = apply_repairs(
        state,
        _decision_table(),
        llm_client=DummyLLM(),
        context_text="context",
    )
    assert result.repair_history == []
    assert result.attempts_by_field == {}
    assert result.final_decision == "ACCEPT"


def test_disease_generalization_requires_substring_parent() -> None:
    raw = "Kras-driven lung cancer"
    alternates = [
        {
            "term_id": "DOID:1612",
            "label": "breast cancer",
            "source": "Human Disease Ontology",
            "confidence": 0.55,
        }
    ]
    state = PipelineState(
        gsm_accession="GSM101",
        final_output=_full_output(disease=raw),
        ontology_matches={"disease": _low_confidence_match(raw, alternates)},
        ontology_failures={"disease": ONTOLOGY_LOW_CONFIDENCE_DISEASE},
    )

    apply_disease_modifier_generalization(state, {})

    assert state.final_output["disease"] == raw
    assert state.ontology_failures.get("disease") == ONTOLOGY_LOW_CONFIDENCE_DISEASE
    assert "disease_generalized_for_ontology" not in state.flags


def test_disease_generalization_uses_top_ranked_alternate_only() -> None:
    raw = "EGFR-mutant lung adenocarcinoma"
    alternates = [
        {
            "term_id": "DOID:9999",
            "label": "sarcoma",
            "source": "Human Disease Ontology",
            "confidence": 0.60,
        },
        {
            "term_id": "DOID:3910",
            "label": "lung adenocarcinoma",
            "source": "Human Disease Ontology",
            "confidence": 0.55,
        },
    ]
    state = PipelineState(
        gsm_accession="GSM102",
        final_output=_full_output(disease=raw),
        ontology_matches={"disease": _low_confidence_match(raw, alternates)},
        ontology_failures={"disease": ONTOLOGY_LOW_CONFIDENCE_DISEASE},
    )

    apply_disease_modifier_generalization(state, {})

    assert state.final_output["disease"] == raw
    assert state.ontology_failures.get("disease") == ONTOLOGY_LOW_CONFIDENCE_DISEASE
