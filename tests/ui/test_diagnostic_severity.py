from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ui.app_streamlit import _append_aggrid_meta_columns, _build_aggrid_options
from ui.schema import CANONICAL_FIELDS


def _base_df(gse: str = "GSE1", gsm: str = "GSM1") -> pd.DataFrame:
    row: dict[str, object] = {
        "gse_accession": gse,
        "gsm_accession": gsm,
    }
    for field in CANONICAL_FIELDS:
        row[field] = f"value-{field}"
    return pd.DataFrame([row])


def _base_curation_record(
    gse: str = "GSE1",
    gsm: str = "GSM1",
    *,
    raw: dict[str, object] | None = None,
) -> dict[str, object]:
    fields = {field: f"value-{field}" for field in CANONICAL_FIELDS}
    return {
        "gse_accession": gse,
        "gsm_accession": gsm,
        "fields": fields,
        "raw": raw or {},
    }


def test_append_aggrid_meta_columns_blocking_and_advisory_split_fields() -> None:
    df = _base_df()
    curation_lookup = {
        ("GSE1", "GSM1"): _base_curation_record(
            raw={
                "rationale": {"primary_failure": "ontology_low_confidence_disease"},
                "validation": {"ontology_failures": {"disease": ["NO_MATCH"]}},
                "flags": ["gse_outlier_tissue_type"],
            }
        )
    }

    updated = _append_aggrid_meta_columns(
        df,
        curation_lookup=curation_lookup,
        evidence_lookup={},
        audit_lookup={},
        flag_summaries={},
        primary_failures={},
    )

    row = updated.iloc[0]
    assert bool(row["__blocking_field_disease"]) is True
    assert bool(row["__advisory_field_tissue_type"]) is True
    assert bool(row["__blocking_field_tissue_type"]) is False
    assert bool(row["__advisory_field_disease"]) is False


def test_append_aggrid_meta_columns_combined_blocking_and_advisory_same_field() -> None:
    df = _base_df()
    curation_lookup = {
        ("GSE1", "GSM1"): _base_curation_record(
            raw={
                "primary_failure": "ontology_low_confidence_disease",
                "validation": {"semantic_errors": {"disease": ["conflict"]}},
                "flags": ["gse_outlier_disease"],
            }
        )
    }

    updated = _append_aggrid_meta_columns(
        df,
        curation_lookup=curation_lookup,
        evidence_lookup={},
        audit_lookup={},
        flag_summaries={},
        primary_failures={},
    )

    row = updated.iloc[0]
    assert bool(row["__blocking_field_disease"]) is True
    assert bool(row["__advisory_field_disease"]) is True


def test_append_aggrid_meta_columns_accept_record_can_show_advisory_without_blocking() -> None:
    df = _base_df()
    curation_lookup = {
        ("GSE1", "GSM1"): _base_curation_record(raw={"flags": ["gse_outlier_disease"]})
    }

    updated = _append_aggrid_meta_columns(
        df,
        curation_lookup=curation_lookup,
        evidence_lookup={},
        audit_lookup={},
        flag_summaries={},
        primary_failures={},
    )

    row = updated.iloc[0]
    assert bool(row["__advisory_field_disease"]) is True
    assert bool(row["__blocking_field_disease"]) is False


def test_append_aggrid_meta_columns_healthy_disease_conflict_is_advisory_only() -> None:
    df = _base_df()
    curation_lookup = {
        ("GSE1", "GSM1"): _base_curation_record(
            raw={"flags": ["healthy_disease_conflict"]}
        )
    }

    updated = _append_aggrid_meta_columns(
        df,
        curation_lookup=curation_lookup,
        evidence_lookup={},
        audit_lookup={},
        flag_summaries={},
        primary_failures={},
    )

    row = updated.iloc[0]
    assert bool(row["__advisory_field_disease"]) is True
    assert bool(row["__blocking_field_disease"]) is False


def test_build_aggrid_options_override_fill_dominates_with_both_markers_present() -> None:
    df = _base_df()
    row = df.iloc[0].to_dict()
    row.update(
        {
            "__row_index": 0,
            "__row_has_flags": True,
            "__primary_failure_color": "",
            "__flag_summary_color": "",
            "Status": "",
            "checked": False,
            "Edited": "",
            "is_edited": False,
            "Review flags": "",
            "Terminal fallbacks": "",
            "Outliers": "",
            "Primary failure": "",
            "Flag summary": "",
            "flagged_fields": "",
        }
    )
    for field in CANONICAL_FIELDS:
        row[f"__override_cell_{field}"] = field == "disease"
        row[f"__blocking_field_{field}"] = field == "disease"
        row[f"__advisory_field_{field}"] = field == "disease"
        row[f"__evidence_flagged_{field}"] = False
        row[f"evidence_flags_{field}"] = []
        row[f"evidence_attempts_{field}"] = 0
        row[f"evidence_status_{field}"] = ""
        row[f"evidence_terminal_{field}"] = False
    options = _build_aggrid_options(pd.DataFrame([row]), edit_mode=True)

    disease_col = next(
        column for column in options["columnDefs"] if column.get("field") == "disease"
    )
    rules = disease_col.get("cellClassRules", {})
    assert "ag-cell-marker-blocking" in rules
    assert "ag-cell-marker-advisory" in rules

    style_js = disease_col["cellStyle"].js_code
    assert 'return { backgroundColor: "#dff4df" };' in style_js
    assert 'return { backgroundColor: "#ffe7cc" };' in style_js
    assert style_js.index("if (isOverridden)") < style_js.index("if (isBlocking)")
