from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agent.config import load_config


def test_postpass_defaults_applied(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("versions: {}\n", encoding="utf-8")

    cfg = load_config(str(config_path))

    postpass_cfg = cfg.get("postpass")
    assert isinstance(postpass_cfg, dict)
    gse_cfg = postpass_cfg.get("gse_consistency")
    assert isinstance(gse_cfg, dict)
    assert gse_cfg.get("enabled") is True
    assert gse_cfg.get("fields") == [
        "data_type",
        "organism",
        "tissue_type",
        "cell_line",
        "disease",
    ]
    assert gse_cfg.get("ignore_values") == ["Unknown", "None", "No", "Healthy"]
    assert gse_cfg.get("outlier_min_samples") == 5
    assert gse_cfg.get("outlier_min_dominant_fraction") == 0.80

    suggestions_cfg = postpass_cfg.get("suggestions")
    assert isinstance(suggestions_cfg, dict)
    assert suggestions_cfg.get("enabled") is False
    assert suggestions_cfg.get("fields") == [
        "data_type",
        "organism",
        "tissue_type",
        "cell_line",
        "disease",
        "treatment",
    ]
    assert suggestions_cfg.get("majority_fraction") == 0.80
    assert suggestions_cfg.get("support_fraction_precision") == 3
