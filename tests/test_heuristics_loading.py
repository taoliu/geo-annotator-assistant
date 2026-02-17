from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from validator.heuristics import get_heuristics


def test_heuristics_loads_required_sections() -> None:
    heuristics = get_heuristics()
    assert "semantic" in heuristics
    assert "consistency" in heuristics

    semantic = heuristics["semantic"]
    semantic_lists = [
        "tissue_cell_keywords",
        "tissue_cell_suffixes",
        "treatment_identity_keywords",
        "treatment_intervention_indicators",
        "treatment_genotype_keywords",
        "treatment_tissue_keywords",
        "disease_cues",
    ]
    for key in semantic_lists:
        assert key in semantic
        assert isinstance(semantic[key], list)
        assert semantic[key]

    consistency = heuristics["consistency"]
    consistency_lists = [
        "single_cell_data_types",
        "single_cell_keywords",
        "sequencing_keywords",
        "disease_keywords",
        "organism_conflicts",
    ]
    for key in consistency_lists:
        assert key in consistency
        assert isinstance(consistency[key], list)
        assert consistency[key]

    assert "microarray_data_type" in consistency
    assert isinstance(consistency["microarray_data_type"], str)
    assert consistency["microarray_data_type"]

    assert "healthy_value" in consistency
    assert isinstance(consistency["healthy_value"], str)
    assert consistency["healthy_value"]
