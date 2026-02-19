from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ui.gse_dropdown import (
    GseDropdownSummary,
    build_gse_dropdown_option_models,
    build_gse_dropdown_summaries,
    format_gse_dropdown_fallback,
)


def test_build_gse_dropdown_summaries_counts_total_flagged_checked() -> None:
    curation_records = [
        {
            "gse_accession": "GSE1",
            "gsm_accession": "GSM1",
            "raw": {"final_decision": "FLAGGED"},
        },
        {
            "gse_accession": "GSE1",
            "gsm_accession": "GSM2",
            "raw": {"final_decision": "ACCEPT"},
        },
        {
            "gse_accession": "GSE2",
            "gsm_accession": "GSM9",
            "raw": {"final_decision": "FLAGGED"},
        },
    ]
    checked_state = {
        ("GSE1", "GSM1"): True,
        ("GSE1", "GSM2"): False,
        ("GSE1", "GSM3"): True,
        ("GSE2", "GSM9"): True,
    }

    summaries = build_gse_dropdown_summaries(curation_records, checked_state)

    assert summaries["GSE1"] == GseDropdownSummary(
        gse_accession="GSE1",
        flagged_count=1,
        checked_count=1,
        total_count=2,
    )
    assert summaries["GSE2"] == GseDropdownSummary(
        gse_accession="GSE2",
        flagged_count=1,
        checked_count=1,
        total_count=1,
    )


def test_format_gse_dropdown_fallback_plain_text_label() -> None:
    summary = GseDropdownSummary(
        gse_accession="GSE12345",
        flagged_count=50,
        checked_count=20,
        total_count=100,
    )

    assert format_gse_dropdown_fallback(summary) == "GSE12345 50/100 20/100"


def test_build_gse_dropdown_option_models_preserves_order_and_defaults() -> None:
    summaries = {
        "GSE2": GseDropdownSummary(
            gse_accession="GSE2",
            flagged_count=1,
            checked_count=2,
            total_count=4,
        ),
        "GSE1": GseDropdownSummary(
            gse_accession="GSE1",
            flagged_count=3,
            checked_count=2,
            total_count=5,
        ),
    }

    models = build_gse_dropdown_option_models(["GSE2", "GSE1", "GSE3"], summaries)

    assert [model.gse_accession for model in models] == ["GSE2", "GSE1", "GSE3"]
    assert models[0].fallback_label == "GSE2 1/4 2/4"
    assert models[1].fallback_label == "GSE1 3/5 2/5"
    assert models[2].fallback_label == "GSE3 0/0 0/0"
