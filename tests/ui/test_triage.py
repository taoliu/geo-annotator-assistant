from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ui.triage import (
    apply_triage_filter,
    build_triage_flags,
    has_overrides,
    is_clean,
    needs_attention,
)


def _clean_evidence() -> dict:
    return {
        "grounding": {
            "data_type": {
                "status": "MATCHED",
                "score": 1.0,
                "match_type": "label_norm_exact",
            },
            "tissue_type": {
                "status": "MATCHED",
                "score": 1.0,
                "match_type": "label_norm_exact",
            },
            "cell_line": {
                "status": "MATCHED",
                "score": 1.0,
                "match_type": "label_norm_exact",
            },
            "disease": {
                "status": "MATCHED",
                "score": 1.0,
                "match_type": "label_norm_exact",
            },
        }
    }


def test_triage_helpers_classify_records() -> None:
    attention_evidence = {
        "evidence_by_field": {
            "disease": {"ontology_status": "LOW_CONFIDENCE"}
        }
    }
    clean_evidence = _clean_evidence()
    overrides = {("GSE1", "GSM1", "disease"): "Cancer"}

    assert needs_attention(attention_evidence)
    assert not needs_attention(clean_evidence)

    assert has_overrides(overrides, "GSE1", "GSM1")
    assert not has_overrides(overrides, "GSE1", "GSM2")

    assert not is_clean(attention_evidence, {})
    assert not is_clean(clean_evidence, {"disease": "Cancer"})
    assert is_clean(clean_evidence, {})


def test_apply_triage_filter() -> None:
    rows = [
        {
            "gse_accession": "GSE1",
            "gsm_accession": "GSM1",
            "data_type": "RNA-seq",
            "organism": "Homo sapiens",
            "tissue_type": "Blood",
            "cell_line": "No",
            "disease": "Healthy",
            "treatment": "No",
        },
        {
            "gse_accession": "GSE1",
            "gsm_accession": "GSM2",
            "data_type": "RNA-seq",
            "organism": "Homo sapiens",
            "tissue_type": "Blood",
            "cell_line": "No",
            "disease": "Healthy",
            "treatment": "No",
        },
    ]
    evidence_lookup = {
        ("GSE1", "GSM1"): {
            "raw": {
                "evidence_by_field": {
                    "disease": {"ontology_status": "NO_MATCH"}
                }
            }
        },
        ("GSE1", "GSM2"): {"raw": _clean_evidence()},
    }
    overrides = {("GSE1", "GSM1", "disease"): "Cancer"}

    triage_flags = build_triage_flags(rows, evidence_lookup, overrides)

    assert len(apply_triage_filter(rows, triage_flags, "All")) == 2
    assert apply_triage_filter(rows, triage_flags, "Needs attention") == [rows[0]]
    assert apply_triage_filter(rows, triage_flags, "Has overrides") == [rows[0]]
    assert apply_triage_filter(rows, triage_flags, "Clean") == [rows[1]]
