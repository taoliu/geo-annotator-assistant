from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ui.evidence import extract_field_evidence


def test_extract_field_evidence_from_grounding() -> None:
    evidence_raw = {
        "grounding": {
            "disease": {
                "raw_value": "lung cancer",
                "normalized_value": "lung cancer",
                "status": "MATCHED",
                "match_type": "synonym_exact",
                "score": 1.0,
                "matched_source": "Human Disease Ontology",
                "selected_source": "NCI Thesaurus",
                "locked": True,
            }
        },
        "canonicalizations": [
            {"field": "disease", "canonical_value": "Lung carcinoma"}
        ],
        "locked_fields": {"disease": {"reason": "ontology_terminal_exact"}},
    }

    items = extract_field_evidence("disease", evidence_raw)

    assert items == [
        {"label": "Raw value", "value": "lung cancer"},
        {"label": "Normalized value", "value": "lung cancer"},
        {"label": "Ontology source", "value": "NCI Thesaurus"},
        {"label": "Match status", "value": "MATCHED"},
        {"label": "Match type", "value": "synonym_exact"},
        {"label": "Score", "value": "1.0"},
        {"label": "Canonical label used", "value": "Lung carcinoma"},
        {"label": "Locked", "value": "true"},
        {"label": "Terminal exact", "value": "true"},
    ]


def test_extract_field_evidence_handles_missing_data() -> None:
    evidence_raw = {
        "evidence_by_field": {"disease": {"ontology_status": "NO_MATCH"}}
    }

    items = extract_field_evidence("disease", evidence_raw)

    assert items == [{"label": "Match status", "value": "NO_MATCH"}]
