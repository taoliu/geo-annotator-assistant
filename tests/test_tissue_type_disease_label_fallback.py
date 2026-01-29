from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agent.ontology_canonicalization import apply_tissue_disease_label_fallback
from agent.state import PipelineState
from validator.ontology_validator import ground_all_fields
import validator.grounders.tissue_type as tissue_grounder


def _disease_label_match(raw: str) -> dict:
    return {
        "status": "FALLBACK",
        "score": None,
        "match_type": "fallback",
        "matched_label": None,
        "matched_term_id": None,
        "matched_source": None,
        "raw_value": raw,
        "matched_via": "disease_label_used_as_tissue",
    }


def _base_output(**overrides: str) -> dict:
    base = {
        "gse_accession": "GSE000111",
        "gsm_accession": "GSM000222",
        "data_type": "RNA-seq",
        "organism": "Homo sapiens",
        "tissue_type": "Lymphoma",
        "cell_line": "No",
        "disease": "Lymphoma",
        "treatment": "None",
    }
    base.update(overrides)
    return base


def test_tissue_disease_label_fallback_applies() -> None:
    state = PipelineState(
        gsm_accession="GSM000222",
        gse_accession="GSE000111",
        final_output=_base_output(),
        ontology_matches={"tissue_type": _disease_label_match("Lymphoma")},
    )

    apply_tissue_disease_label_fallback(state, {})

    assert state.final_output["tissue_type"] == "Unknown"
    assert "tissue_type_disease_label_used_as_tissue" in state.flags
    assert state.locked_fields["tissue_type"]["label"] == "Unknown"


def test_tissue_disease_label_detection_skips_grounder(monkeypatch) -> None:
    def _raise(*_args, **_kwargs):
        raise AssertionError("ground_tissue_type should not be called")

    monkeypatch.setattr(tissue_grounder, "ground_tissue_type", _raise, raising=False)

    llm_output = {
        "organism": "Homo sapiens",
        "disease": "Lymphoma",
        "tissue_type": "Lymphoma",
        "cell_line": "No",
        "data_type": "RNA-seq",
    }

    matches, failures = ground_all_fields(llm_output, "", {})

    assert "tissue_type" not in failures
    assert matches["tissue_type"].status == "FALLBACK"
    assert matches["tissue_type"].matched_via == "disease_label_used_as_tissue"


def test_tissue_disease_label_detection_skips_non_disease_terms(monkeypatch) -> None:
    def _dummy(*args, **kwargs):
        return None

    monkeypatch.setattr(tissue_grounder, "ground_tissue_type", _dummy, raising=False)

    llm_output = {
        "organism": "Homo sapiens",
        "disease": "Breast cancer",
        "tissue_type": "cancer associated fibroblasts",
        "cell_line": "No",
        "data_type": "RNA-seq",
    }

    matches, _ = ground_all_fields(llm_output, "", {})

    assert matches["tissue_type"].matched_via != "disease_label_used_as_tissue"
