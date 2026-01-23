from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agent.config import load_config
from agent.gse_postpass import (
    apply_gse_consistency_postpass,
    apply_gse_field_values_summary,
)


def _base_annotation(
    gsm_accession: str,
    gse_accession: str,
    data_type: str = "RNA-seq",
    organism: str = "Homo sapiens",
    tissue_type: str = "Blood",
    cell_line: str = "No",
    disease: str = "Healthy",
) -> dict:
    return {
        "gse_accession": gse_accession,
        "gsm_accession": gsm_accession,
        "data_type": data_type,
        "organism": organism,
        "tissue_type": tissue_type,
        "cell_line": cell_line,
        "disease": disease,
        "treatment": "None",
    }


def _base_audit(gsm_accession: str, gse_accession: str) -> dict:
    return {"gsm_accession": gsm_accession, "gse_accession": gse_accession}


def test_gse_consistency_excludes_placeholders() -> None:
    cfg = load_config(str(ROOT / "config" / "example_config.yaml"))
    cfg["postpass"]["gse_consistency"]["outlier_min_samples"] = 10

    annotations = [
        _base_annotation("GSM1", "GSE1", tissue_type="Unknown"),
        _base_annotation("GSM2", "GSE1", tissue_type="Liver"),
        _base_annotation("GSM3", "GSE1", tissue_type="Liver"),
        _base_annotation("GSM4", "GSE1", tissue_type="Healthy"),
        _base_annotation("GSM5", "GSE1", tissue_type="Heart"),
    ]
    audits = [_base_audit(row["gsm_accession"], "GSE1") for row in annotations]

    report = apply_gse_consistency_postpass(annotations, audits, cfg)

    assert report is not None
    tissue_report = report["fields"]["tissue_type"]
    assert tissue_report["n_non_placeholder"] == 3
    assert tissue_report["counts"] == {"Liver": 2, "Heart": 1}
    assert tissue_report["outliers"] == []


def test_gse_consistency_flags_outliers() -> None:
    cfg = load_config(str(ROOT / "config" / "example_config.yaml"))

    annotations = [
        _base_annotation("GSM1", "GSE2", disease="Cancer"),
        _base_annotation("GSM2", "GSE2", disease="Cancer"),
        _base_annotation("GSM3", "GSE2", disease="Cancer"),
        _base_annotation("GSM4", "GSE2", disease="Cancer"),
        _base_annotation("GSM5", "GSE2", disease="Diabetes"),
    ]
    audits = [_base_audit(row["gsm_accession"], "GSE2") for row in annotations]

    report = apply_gse_consistency_postpass(annotations, audits, cfg)

    assert report is not None
    disease_report = report["fields"]["disease"]
    assert disease_report["outliers"] == ["GSM5"]
    assert audits[-1]["gse_outlier_disease"] is True
    assert "gse_outlier_disease" not in audits[0]


def test_gse_consistency_requires_dominant_fraction() -> None:
    cfg = load_config(str(ROOT / "config" / "example_config.yaml"))

    annotations = [
        _base_annotation("GSM1", "GSE3", organism="Homo sapiens"),
        _base_annotation("GSM2", "GSE3", organism="Homo sapiens"),
        _base_annotation("GSM3", "GSE3", organism="Mus musculus"),
        _base_annotation("GSM4", "GSE3", organism="Mus musculus"),
        _base_annotation("GSM5", "GSE3", organism="Homo sapiens"),
    ]
    audits = [_base_audit(row["gsm_accession"], "GSE3") for row in annotations]

    report = apply_gse_consistency_postpass(annotations, audits, cfg)

    assert report is not None
    organism_report = report["fields"]["organism"]
    assert organism_report["outliers"] == []
    assert all("gse_outlier_organism" not in audit for audit in audits)


def test_gse_field_values_summary_ordering() -> None:
    cfg = load_config(str(ROOT / "config" / "example_config.yaml"))

    annotations = [
        _base_annotation("GSM1", "GSE4", tissue_type="Liver"),
        _base_annotation("GSM2", "GSE4", tissue_type="Heart"),
        _base_annotation("GSM3", "GSE4", tissue_type="Liver"),
        _base_annotation("GSM4", "GSE4", tissue_type="Brain"),
        _base_annotation("GSM5", "GSE4", tissue_type="Heart"),
        _base_annotation("GSM6", "GSE4", tissue_type="Unknown"),
    ]

    report = apply_gse_field_values_summary(annotations, cfg)

    assert report is not None
    tissue_values = report["fields"]["tissue_type"]
    assert tissue_values == ["Heart", "Liver", "Brain"]
