from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agent.run_single import _apply_locked_field_values
from agent.state import PipelineState


def test_locked_field_value_overrides_final_output() -> None:
    state = PipelineState(gsm_accession="GSMLOCK", gse_accession="GSELOCK")
    state.final_output = {
        "gse_accession": "GSELOCK",
        "gsm_accession": "GSMLOCK",
        "data_type": "RNA-seq",
        "organism": "Homo sapiens",
        "tissue_type": "Tumor",
        "cell_line": "No",
        "disease": "Healthy",
        "treatment": "None",
    }
    state.locked_fields = {
        "tissue_type": {
            "label": "Unknown",
            "reason": "tissue_type_non_anatomical_placeholder",
            "original_value": "Tumor",
        }
    }

    _apply_locked_field_values(state)

    assert state.final_output["tissue_type"] == "Unknown"
