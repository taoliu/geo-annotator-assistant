from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ui.override_safety import (
    build_override_diff,
    field_is_editable,
    requires_override_confirmation,
)
from ui.overrides import clear_override, overrides_for_gsm


def test_field_is_editable_even_with_high_confidence() -> None:
    evidence_raw = {
        "locked_fields": {"disease": {"reason": "ontology_terminal_exact"}},
        "canonicalizations": [{"field": "disease", "canonical_value": "Cancer"}],
        "grounding": {
            "disease": {
                "status": "MATCHED",
                "score": 1.0,
                "match_type": "synonym_exact",
                "locked": True,
            }
        },
    }

    assert field_is_editable(True, "disease", evidence_raw)


def test_requires_override_confirmation_gates_on_high_confidence() -> None:
    high_confidence = {
        "locked_fields": {"cell_line": {"reason": "ontology_terminal_exact"}},
    }
    low_confidence = {
        "evidence_by_field": {
            "cell_line": {"ontology_status": "LOW_CONFIDENCE"}
        }
    }

    assert requires_override_confirmation("cell_line", high_confidence)
    assert not requires_override_confirmation("cell_line", low_confidence)


def test_build_override_diff_and_revert() -> None:
    overrides = {("GSE1", "GSM1", "disease"): "Cancer"}
    selected = overrides_for_gsm(overrides, "GSE1", "GSM1")

    diff = build_override_diff("disease", "Healthy", selected)

    assert diff is not None
    assert diff["backend_value"] == "Healthy"
    assert diff["override_value"] == "Cancer"

    overrides = clear_override(overrides, "GSE1", "GSM1", "disease")
    selected = overrides_for_gsm(overrides, "GSE1", "GSM1")

    assert build_override_diff("disease", "Healthy", selected) is None
