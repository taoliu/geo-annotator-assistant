from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ui.flags import build_flags_index, extract_field_flags
from ui.styling import style_curation_table


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
        "disease": ["ontology_status:NO_MATCH", "rare_value"],
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
