from __future__ import annotations

from agent.ontology_canonicalization import apply_llm_non_answer_placeholders
from agent.state import PipelineState
from validator.non_answer_placeholders import is_llm_non_answer_placeholder
from validator.ontology_validator import ground_all_fields
from validator.semantic_validator import semantic_validate


def test_non_answer_placeholder_detection() -> None:
    assert is_llm_non_answer_placeholder("Not sure") is True
    assert is_llm_non_answer_placeholder("n/a") is True
    assert is_llm_non_answer_placeholder("?") is True
    assert is_llm_non_answer_placeholder("unknown") is True
    assert is_llm_non_answer_placeholder("healthy") is False


def test_ground_all_fields_skips_non_answer_placeholder() -> None:
    llm_output = {
        "data_type": "RNA-seq",
        "tissue_type": "Blood",
        "cell_line": "No",
        "disease": "Not sure",
    }
    matches, failures = ground_all_fields(llm_output, "", {})

    match = matches["disease"]
    assert match.status == "FALLBACK"
    assert match.matched_via == "llm_non_answer_placeholder"
    assert "disease" not in failures


def test_semantic_validator_skips_non_answer_placeholder() -> None:
    parsed = {
        "tissue_type": "Not clear",
        "treatment": "N/A",
        "cell_line": "?",
        "disease": "Unknown",
    }
    errs = semantic_validate(parsed, "")
    assert errs == {}


def test_apply_llm_non_answer_placeholders() -> None:
    state = PipelineState(gsm_accession="GSM000")
    state.final_output = {
        "gse_accession": "GSE000",
        "gsm_accession": "GSM000",
        "data_type": "Unknown",
        "organism": "Not provided",
        "tissue_type": "Not clear",
        "cell_line": "?",
        "disease": "Not sure",
        "treatment": "N/A",
    }
    state.semantic_errors = {"disease": ["disease_inferred_without_evidence"]}
    state.ontology_failures = {"disease": "ontology_low_confidence_disease"}

    apply_llm_non_answer_placeholders(state, None)

    assert state.final_output["disease"] == "Unknown"
    assert state.final_output["treatment"] == "None"
    assert state.final_output["tissue_type"] == "Unknown"
    assert state.final_output["cell_line"] == "Unknown"
    assert state.final_output["organism"] == "Unknown"
    assert state.final_output["data_type"] == "Unknown"
    assert state.locked_fields["disease"]["reason"] == "llm_non_answer_placeholder"
    assert "llm_non_answer_disease" in state.flags
    assert "llm_non_answer_tissue_type" in state.flags
    assert "llm_non_answer_cell_line" in state.flags
    assert "disease" not in state.semantic_errors
    assert "disease" not in state.ontology_failures
