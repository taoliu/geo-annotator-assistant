from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ui.ontology_tooltips import (
    COMPOSITE_MATCHED_VIA,
    COMPOSITE_PARTIAL_MATCHED_VIA,
    build_composite_tooltip_payload,
    is_composite_match,
)


def test_is_composite_match_uses_matched_via() -> None:
    assert is_composite_match({"matched_via": COMPOSITE_MATCHED_VIA}) is True
    assert is_composite_match({"matched_via": COMPOSITE_PARTIAL_MATCHED_VIA}) is True
    assert is_composite_match({"matched_via": "label_norm"}) is False
    assert is_composite_match({"matched_term_id": None}) is False


def test_build_composite_tooltip_payload_for_matched_case() -> None:
    match = {
        "status": "MATCHED",
        "matched_via": COMPOSITE_MATCHED_VIA,
        "selection_rule": "all_components_required_v1",
        "composite_resolution": {
            "selection_rule": "all_components_required_v1",
            "matched_components": 2,
            "total_components": 2,
            "fragment_matches": [
                {
                    "label": "colon",
                    "term_id": "UBERON:0001155",
                    "status": "MATCHED",
                },
                {
                    "label": "rectum",
                    "term_id": "UBERON:0001052",
                    "status": "MATCHED",
                },
            ],
        },
    }

    payload = build_composite_tooltip_payload(match)
    assert payload is not None
    assert payload["matched_via"] == COMPOSITE_MATCHED_VIA
    assert payload["selection_rule"] == "all_components_required_v1"
    assert payload["components_key"] == "Matched components (2/2)"
    assert payload["components_value"] == (
        "• colon (UBERON:0001155)\n"
        "• rectum (UBERON:0001052)"
    )


def test_build_composite_tooltip_payload_for_partial_case() -> None:
    match = {
        "status": "LOW_CONFIDENCE",
        "matched_via": COMPOSITE_PARTIAL_MATCHED_VIA,
        "selection_rule": "all_components_required_v1",
        "composite_resolution": {
            "selection_rule": "all_components_required_v1",
            "matched_components": 1,
            "total_components": 2,
            "fragment_matches": [
                {
                    "label": "colon",
                    "term_id": "UBERON:0001155",
                    "status": "MATCHED",
                },
                {
                    "raw_fragment": "mystery tissue",
                    "status": "NO_MATCH",
                },
            ],
        },
    }

    payload = build_composite_tooltip_payload(match)
    assert payload is not None
    assert payload["components_key"] == "Matched components (1/2)"
    assert payload["components_value"] == "• colon (UBERON:0001155)"


def test_build_composite_tooltip_payload_non_composite_is_none() -> None:
    assert (
        build_composite_tooltip_payload(
            {
                "status": "MATCHED",
                "matched_via": "label_norm",
                "matched_term_id": "UBERON:0001155",
            }
        )
        is None
    )
