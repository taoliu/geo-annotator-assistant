from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ui.state import (
    build_details_context,
    default_modal_state,
    details_render_mode,
    index_audit_records,
    index_curation_records,
    index_evidence_records,
    index_suggestion_records,
    resolve_selected_key,
    update_modal_state,
)


def _row(gse: str, gsm: str) -> dict:
    return {
        "gse_accession": gse,
        "gsm_accession": gsm,
        "data_type": "RNA-seq",
        "organism": "Homo sapiens",
        "tissue_type": "Blood",
        "cell_line": "No",
        "disease": "Healthy",
        "treatment": "No",
    }


def _curation_record(gse: str, gsm: str) -> dict:
    return {
        "gse_accession": gse,
        "gsm_accession": gsm,
        "fields": {
            "data_type": "RNA-seq",
            "organism": "Homo sapiens",
            "tissue_type": "Blood",
            "cell_line": "No",
            "disease": "Healthy",
            "treatment": "No",
        },
        "raw": {"gse_accession": gse, "gsm_accession": gsm},
    }


def test_selection_updates_modal_state() -> None:
    rows = [_row("GSE1", "GSM1"), _row("GSE2", "GSM2")]

    selected_key = resolve_selected_key(rows, [1])
    state = update_modal_state(default_modal_state(), selected_key)

    assert state["active"] == ("GSE2", "GSM2")
    assert state["is_open"] is True


def test_modal_context_binds_active_record() -> None:
    curation_records = [_curation_record("GSE1", "GSM1")]
    evidence_records = [
        {
            "gse_accession": "GSE1",
            "gsm_accession": "GSM1",
            "raw": {"evidence": True},
        }
    ]
    audit_records = [
        {
            "gse_accession": "GSE1",
            "gsm_accession": "GSM1",
            "raw": {"llm_parsed_outputs": []},
        }
    ]
    suggestions_records = [
        {
            "gse_accession": "GSE1",
            "gsm_accession": "GSM1",
            "field": "disease",
            "raw": {"field": "disease", "value": "x"},
        }
    ]
    flags_by_gsm = {("GSE1", "GSM1"): {"disease": ["missing"]}}
    overrides = {("GSE1", "GSM1", "disease"): "Flu"}

    context = build_details_context(
        ("GSE1", "GSM1"),
        index_curation_records(curation_records),
        index_evidence_records(evidence_records),
        index_audit_records(audit_records),
        index_suggestion_records(suggestions_records),
        flags_by_gsm,
        overrides,
    )

    assert context["curation"] == curation_records[0]
    assert context["evidence"] == evidence_records[0]
    assert context["selected_overrides"]["disease"] == "Flu"
    assert context["effective_fields"]["disease"] == "Flu"


def test_details_render_mode_is_modal() -> None:
    assert details_render_mode() == "modal"
