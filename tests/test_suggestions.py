from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agent.config import load_config
from agent.suggestions import build_gse_suggestions
from agent.writer import write_jsonl


def _load_cfg() -> dict:
    cfg = load_config(str(ROOT / "config" / "example_config.yaml"))
    cfg.setdefault("postpass", {}).setdefault("suggestions", {})["enabled"] = True
    return cfg


def _make_record(gse: str, gsm: str, disease: str) -> dict:
    return {
        "gse_accession": gse,
        "gsm_accession": gsm,
        "data_type": "RNA",
        "organism": "Homo sapiens",
        "tissue_type": "Liver",
        "cell_line": "No",
        "disease": disease,
        "treatment": "None",
    }


def test_suggestions_majority_outlier() -> None:
    cfg = _load_cfg()
    annotations = []
    audits = []
    for idx in range(1, 11):
        disease = "Healthy" if idx < 10 else "Hepatocellular carcinoma"
        record = _make_record("GSE12345", f"GSM{idx:06d}", disease)
        annotations.append(record)
        audits.append({"final_output": dict(record)})

    suggestions = build_gse_suggestions(annotations, audits, cfg, emit_suggestions=True)
    outliers = [
        item
        for item in suggestions
        if item["gsm_accession"] == "GSM000010" and item["field"] == "disease"
    ]

    assert len(outliers) == 1
    suggestion = outliers[0]
    assert suggestion["reason"] == "value_outlier_within_gse"
    assert suggestion["current_value"] == "Hepatocellular carcinoma"
    assert suggestion["suggested_value"] == "Healthy"
    assert suggestion["support_count"] == 9
    assert suggestion["total_count"] == 10
    assert suggestion["support_fraction"] == 0.9


def test_suggestions_singleton_rule() -> None:
    cfg = _load_cfg()
    annotations = []
    audits = []
    values = ["A", "A", "A", "B", "C"]
    for idx, disease in enumerate(values, start=1):
        record = _make_record("GSE99999", f"GSM{idx:06d}", disease)
        annotations.append(record)
        audits.append({"final_output": dict(record)})

    suggestions = build_gse_suggestions(annotations, audits, cfg, emit_suggestions=True)
    singleton = [
        item
        for item in suggestions
        if item["gsm_accession"] == "GSM000004" and item["field"] == "disease"
    ]

    assert len(singleton) == 1
    suggestion = singleton[0]
    assert suggestion["reason"] == "singletons_within_gse"
    assert suggestion["current_value"] == "B"
    assert suggestion["suggested_value"] == "A"
    assert suggestion["support_count"] == 3
    assert suggestion["total_count"] == 5
    assert suggestion["support_fraction"] == 0.6


def test_suggestions_deterministic(tmp_path: Path) -> None:
    cfg = _load_cfg()
    annotations = []
    audits = []
    values = ["X", "X", "Y", "X"]
    for idx, disease in enumerate(values, start=1):
        record = _make_record("GSE24680", f"GSM{idx:06d}", disease)
        annotations.append(record)
        audits.append({"final_output": dict(record)})

    first = build_gse_suggestions(annotations, audits, cfg, emit_suggestions=True)
    second = build_gse_suggestions(annotations, audits, cfg, emit_suggestions=True)

    first_path = tmp_path / "first.jsonl"
    second_path = tmp_path / "second.jsonl"
    write_jsonl(str(first_path), first)
    write_jsonl(str(second_path), second)

    assert first_path.read_bytes() == second_path.read_bytes()
