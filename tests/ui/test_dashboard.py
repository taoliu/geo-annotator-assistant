from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ui.dashboard import build_dashboard_item, map_field_badges
from ui.overrides import apply_overrides_to_record


def test_map_field_badges_collects_available_signals() -> None:
    evidence_raw = {
        "evidence_by_field": {
            "data_type": {"ontology_status": "LOW_CONFIDENCE"},
            "disease": {"ontology_status": "NO_MATCH"},
        },
        "grounding": {
            "cell_line": {
                "status": "MATCHED",
                "score": 1.0,
                "match_type": "label_norm_exact",
            },
            "tissue_type": {
                "status": "MATCHED",
                "score": 1.0,
                "match_type": "label_exact",
                "canonical_label_used": "blood",
                "locked": True,
            },
        },
        "canonicalizations": [{"field": "tissue_type"}],
        "locked_fields": {"tissue_type": {"reason": "ontology_terminal_exact"}},
    }
    curation_raw = {
        "terminal_fallback_fields": ["disease"],
        "attempts_by_field": {"data_type": 1},
    }
    overrides = {"cell_line": "Myc-CaP"}

    assert map_field_badges("data_type", evidence_raw, overrides, curation_raw) == [
        "REPAIRED",
        "AMBIG",
    ]
    assert map_field_badges("disease", evidence_raw, overrides, curation_raw) == [
        "TERMINAL",
        "NO-MATCH",
    ]
    assert map_field_badges("cell_line", evidence_raw, overrides, curation_raw) == [
        "OVERRIDDEN",
        "TERM",
    ]
    assert map_field_badges("tissue_type", evidence_raw, overrides, curation_raw) == [
        "LOCKED",
        "CANON",
        "TERM",
    ]


def test_build_dashboard_item_override_precedence() -> None:
    selection_key = ("GSE1", "GSM1")
    curation = {
        "gse_accession": "GSE1",
        "gsm_accession": "GSM1",
        "fields": {
            "data_type": "RNA-seq",
            "organism": "Homo sapiens",
            "tissue_type": "Blood",
            "cell_line": "No",
            "disease": "Healthy",
            "treatment": "No",
        },
        "raw": {},
    }
    overrides = {"data_type": "ChIP-seq"}
    effective_fields = apply_overrides_to_record(curation, overrides)

    item = build_dashboard_item(
        "data_type",
        selection_key,
        curation,
        effective_fields,
        None,
        overrides,
    )

    assert item["value"] == "ChIP-seq"
    assert "OVERRIDDEN" in item["badges"]
