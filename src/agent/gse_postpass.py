"""GSE post-pass consistency report and outlier flags."""

from __future__ import annotations

from typing import Any, Dict, List


def _get_gse_consistency_cfg(cfg: dict) -> Dict[str, Any]:
    postpass_cfg = cfg.get("postpass") if isinstance(cfg.get("postpass"), dict) else {}
    gse_cfg = (
        postpass_cfg.get("gse_consistency")
        if isinstance(postpass_cfg.get("gse_consistency"), dict)
        else {}
    )
    return gse_cfg


def _resolve_gse_accession(annotations: List[Dict[str, Any]]) -> str:
    gse_values = {
        record.get("gse_accession")
        for record in annotations
        if record.get("gse_accession")
    }
    if len(gse_values) == 1:
        return next(iter(gse_values))
    return "Unknown"


def apply_gse_consistency_postpass(
    annotations: List[Dict[str, Any]],
    audits: List[Dict[str, Any]],
    cfg: dict,
) -> Dict[str, Any] | None:
    gse_cfg = _get_gse_consistency_cfg(cfg)
    if not gse_cfg.get("enabled", True):
        return None

    fields = gse_cfg.get("fields")
    if not isinstance(fields, list):
        fields = []
    ignore_values = gse_cfg.get("ignore_values")
    if not isinstance(ignore_values, list):
        ignore_values = []
    ignore_set = set(value for value in ignore_values if isinstance(value, str))

    outlier_min_samples = int(gse_cfg.get("outlier_min_samples", 5))
    outlier_min_dominant_fraction = float(
        gse_cfg.get("outlier_min_dominant_fraction", 0.80)
    )

    audit_by_gsm: Dict[str, Dict[str, Any]] = {}
    for audit in audits:
        gsm_accession = audit.get("gsm_accession")
        if gsm_accession and gsm_accession not in audit_by_gsm:
            audit_by_gsm[gsm_accession] = audit

    report_fields: Dict[str, Any] = {}
    for field in fields:
        counts: Dict[str, int] = {}
        for record in annotations:
            value = record.get(field)
            if not isinstance(value, str) or value in ignore_set:
                continue
            counts[value] = counts.get(value, 0) + 1

        n_non_placeholder = sum(counts.values())
        dominant_value = None
        dominant_fraction = 0.0
        if counts:
            dominant_value, dominant_count = max(
                counts.items(),
                key=lambda item: (item[1], item[0]),
            )
            dominant_fraction = dominant_count / n_non_placeholder

        outliers: List[str] = []
        if (
            n_non_placeholder >= outlier_min_samples
            and dominant_fraction >= outlier_min_dominant_fraction
            and dominant_value is not None
        ):
            for record in annotations:
                value = record.get(field)
                if not isinstance(value, str) or value in ignore_set:
                    continue
                if value == dominant_value:
                    continue
                gsm_accession = record.get("gsm_accession")
                if not gsm_accession:
                    continue
                outliers.append(gsm_accession)
                audit = audit_by_gsm.get(gsm_accession)
                if audit is not None:
                    audit[f"gse_outlier_{field}"] = True

        report_fields[field] = {
            "n_non_placeholder": n_non_placeholder,
            "dominant_value": dominant_value,
            "dominant_fraction": dominant_fraction,
            "counts": counts,
            "outliers": outliers,
        }

    return {
        "gse_accession": _resolve_gse_accession(annotations),
        "n_total": len(annotations),
        "ignore_values": ignore_values,
        "fields": report_fields,
    }
