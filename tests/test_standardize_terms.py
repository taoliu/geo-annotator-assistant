from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agent.standardize_terms import REQUIRED_GSM_FIELDS, standardize_terms_records
from validator.ontology_match import OntologyMatch

import validator.grounders.cell_line as cell_line_grounder


def _config(*, canonicalize: bool) -> dict:
    return {
        "rag": {
            "ontology": {
                "canonicalize_terminal_exact_labels": canonicalize,
            }
        }
    }


def _record(**overrides) -> dict:
    base = {
        "gse_accession": "GSE000",
        "gsm_accession": "GSM000",
        "data_type": "RNA-Seq",
        "organism": "Homo sapiens",
        "tissue_type": "Heart",
        "cell_line": "Myccap",
        "disease": "Healthy",
        "treatment": "None",
    }
    base.update(overrides)
    return base


def _terminal_match(raw_value: str) -> OntologyMatch:
    return OntologyMatch(
        field="cell_line",
        raw_value=raw_value,
        ontology="Cellosaurus",
        status="MATCHED",
        matched_term_id="CVCL:J703",
        matched_label="Myc-CaP",
        matched_source="Cellosaurus",
        match_type="label_norm_exact",
        score=1.0,
        alternates=[],
    )


def test_standardize_terms_canonicalizes_terminal_exact(monkeypatch) -> None:
    def dummy_grounder(raw_value, context_text, config):
        return _terminal_match(raw_value)

    monkeypatch.setattr(
        cell_line_grounder,
        "ground_cell_line",
        dummy_grounder,
        raising=False,
    )

    outputs, audits = standardize_terms_records(
        [_record()],
        _config(canonicalize=True),
    )

    assert outputs[0]["cell_line"] == "Myc-CaP"
    assert (
        audits[0]["grounding"]["cell_line"]["canonical_label_used"] == "Myc-CaP"
    )


def test_standardize_terms_canonicalize_disabled(monkeypatch) -> None:
    def dummy_grounder(raw_value, context_text, config):
        return _terminal_match(raw_value)

    monkeypatch.setattr(
        cell_line_grounder,
        "ground_cell_line",
        dummy_grounder,
        raising=False,
    )

    outputs, audits = standardize_terms_records(
        [_record()],
        _config(canonicalize=False),
    )

    assert outputs[0]["cell_line"] == "Myccap"
    assert audits[0]["grounding"]["cell_line"]["canonical_label_used"] is None


def test_standardize_terms_field_selection_skips_unlisted(monkeypatch) -> None:
    def should_not_call(*args, **kwargs):
        raise AssertionError("ground_cell_line should not be called")

    monkeypatch.setattr(
        cell_line_grounder,
        "ground_cell_line",
        should_not_call,
        raising=False,
    )

    outputs, audits = standardize_terms_records(
        [_record()],
        _config(canonicalize=False),
        fields=["data_type"],
    )

    assert outputs[0]["cell_line"] == "Myccap"
    assert audits[0]["grounding"]["cell_line"]["status"] == "SKIPPED"


def test_standardize_terms_output_schema_exact_fields() -> None:
    outputs, _ = standardize_terms_records(
        [_record(extra_field="ignore me")],
        _config(canonicalize=False),
    )

    output_keys = set(outputs[0].keys())
    assert output_keys == set(REQUIRED_GSM_FIELDS)
