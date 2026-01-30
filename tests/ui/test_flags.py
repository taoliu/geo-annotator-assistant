from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ui.flags import (
    FLAG_CATEGORY_INFO,
    FLAG_CATEGORY_POLICY,
    FLAG_CATEGORY_REVIEW,
    build_flag_category_summary,
    build_flags_index,
    categorize_flag,
    extract_field_flags,
    flag_tooltip,
    primary_failure_tooltip,
)
from ui.styling import active_row_style, style_curation_table


def test_extract_field_flags_uses_explicit_signals() -> None:
    evidence_raw = {
        "evidence_by_field": {
            "data_type": {
                "flags": ["assay_platform_conflict"],
                "terminal_fallback": False,
                "ontology_status": "MATCHED",
            },
            "cell_line": {
                "flags": [],
                "terminal_fallback": True,
                "ontology_status": "",
            },
            "disease": {
                "flags": ["rare_value"],
                "terminal_fallback": False,
                "ontology_status": "NO_MATCH",
            },
        }
    }

    flags = extract_field_flags(evidence_raw)

    assert flags == {
        "data_type": ["assay_platform_conflict"],
        "cell_line": ["terminal_fallback"],
        "disease": ["rare_value", "ontology_status:NO_MATCH"],
    }


def test_build_flags_index_deterministic() -> None:
    records = [
        {
            "gse_accession": "GSE1",
            "gsm_accession": "GSM1",
            "raw": {
                "evidence_by_field": {
                    "disease": {"flags": ["flag_a"], "terminal_fallback": False}
                }
            },
        },
        {
            "gse_accession": "GSE1",
            "gsm_accession": "GSM2",
            "raw": {
                "evidence_by_field": {
                    "tissue_type": {
                        "flags": [],
                        "terminal_fallback": True,
                        "ontology_status": "",
                    }
                }
            },
        },
    ]

    first = build_flags_index(records)
    second = build_flags_index(list(reversed(records)))

    assert first == second


def test_style_curation_table_highlights_flagged_cell() -> None:
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
        }
    ]
    df = pd.DataFrame(rows)
    flags_by_gsm = {("GSE1", "GSM1"): {"disease": ["flag"]}}

    styler = style_curation_table(df, flags_by_gsm)
    html = styler.to_html()

    assert "#fff3cd" in html


def test_active_row_style_marks_selected_row() -> None:
    assert active_row_style(1, 1)
    assert active_row_style(0, 1) == ""


def test_style_curation_table_highlights_active_row() -> None:
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
        }
    ]
    df = pd.DataFrame(rows)

    styler = style_curation_table(df, {}, active_row_idx=0)
    html = styler.to_html()

    assert "#e8f4ff" in html


def test_categorize_flag_known_patterns() -> None:
    assert categorize_flag("terminal_fallback") == FLAG_CATEGORY_POLICY
    assert categorize_flag("ontology_low_confidence_disease") == FLAG_CATEGORY_REVIEW
    assert categorize_flag("gse_outlier_disease") == FLAG_CATEGORY_INFO


def test_build_flag_category_summary_counts() -> None:
    summary = build_flag_category_summary(
        ["tissue_type_non_anatomical_placeholder", "disease_generalized_for_ontology"],
        {"disease": ["ontology_status:NO_MATCH"]},
    )

    assert summary["counts"][FLAG_CATEGORY_POLICY] == 1
    assert summary["counts"][FLAG_CATEGORY_REVIEW] == 1
    assert summary["counts"][FLAG_CATEGORY_INFO] == 1
    assert summary["highest"] == FLAG_CATEGORY_POLICY


def test_flag_tooltip_includes_category_and_info() -> None:
    tooltip = flag_tooltip("ontology_low_confidence_disease")

    assert "Category:" in tooltip
    assert "Flags are informational only." in tooltip


def test_primary_failure_tooltip_mentions_determinism() -> None:
    tooltip = primary_failure_tooltip("format_unrepaired")

    assert "deterministically" in tooltip.lower()
    assert "secondary flags still apply" in tooltip.lower()
