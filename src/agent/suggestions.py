"""Cross-GSM suggestion engine for deterministic, advisory outputs."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, Iterable, List, Tuple

_SUGGESTION_FIELDS: Tuple[str, ...] = (
    "data_type",
    "organism",
    "tissue_type",
    "cell_line",
    "disease",
    "treatment",
)

_DEFAULT_MAJORITY_FRACTION = 0.80
_DEFAULT_SUPPORT_FRACTION_PRECISION = 3

_REASON_OUTLIER = "value_outlier_within_gse"
_REASON_SINGLETON = "singletons_within_gse"


def _get_suggestions_cfg(cfg: dict) -> Dict[str, Any]:
    postpass_cfg = cfg.get("postpass") if isinstance(cfg.get("postpass"), dict) else {}
    suggestions_cfg = (
        postpass_cfg.get("suggestions")
        if isinstance(postpass_cfg.get("suggestions"), dict)
        else {}
    )
    return suggestions_cfg


def _resolve_final_record(annotation: dict, audit: dict) -> dict:
    final_output = audit.get("final_output")
    if not isinstance(final_output, dict):
        final_output = annotation if isinstance(annotation, dict) else {}

    record = dict(final_output)
    for key in ("gse_accession", "gsm_accession"):
        if not record.get(key):
            value = None
            if isinstance(audit, dict):
                value = audit.get(key)
            if not value and isinstance(annotation, dict):
                value = annotation.get(key)
            if isinstance(value, str) and value:
                record[key] = value
    return record


def _iter_final_records(
    annotations: List[Dict[str, Any]],
    audits: List[Dict[str, Any]],
) -> Iterable[Dict[str, Any]]:
    total_rows = max(len(annotations), len(audits))
    for idx in range(total_rows):
        annotation = annotations[idx] if idx < len(annotations) else {}
        audit = audits[idx] if idx < len(audits) else {}
        if not isinstance(annotation, dict):
            annotation = {}
        if not isinstance(audit, dict):
            audit = {}
        yield _resolve_final_record(annotation, audit)


def _round_support_fraction(count: int, total: int, precision: int) -> float:
    if total <= 0:
        return 0.0
    if precision < 0:
        precision = 0
    quant = Decimal("1").scaleb(-precision)
    value = Decimal(count) / Decimal(total)
    return float(value.quantize(quant, rounding=ROUND_HALF_UP))


def build_gse_suggestions(
    annotations: List[Dict[str, Any]],
    audits: List[Dict[str, Any]],
    cfg: dict,
    emit_suggestions: bool | None = None,
) -> List[Dict[str, Any]]:
    """Build advisory cross-GSM suggestions from final outputs only."""
    suggestions_cfg = _get_suggestions_cfg(cfg)
    enabled_cfg = bool(suggestions_cfg.get("enabled", False))
    if emit_suggestions is None:
        enabled = enabled_cfg
    else:
        enabled = emit_suggestions
    if not enabled:
        return []

    fields = suggestions_cfg.get("fields")
    if not isinstance(fields, list):
        fields = list(_SUGGESTION_FIELDS)

    majority_fraction = suggestions_cfg.get("majority_fraction", _DEFAULT_MAJORITY_FRACTION)
    try:
        majority_fraction = float(majority_fraction)
    except (TypeError, ValueError):
        majority_fraction = _DEFAULT_MAJORITY_FRACTION

    precision = suggestions_cfg.get(
        "support_fraction_precision", _DEFAULT_SUPPORT_FRACTION_PRECISION
    )
    try:
        precision = int(precision)
    except (TypeError, ValueError):
        precision = _DEFAULT_SUPPORT_FRACTION_PRECISION

    records_by_gse: Dict[str, List[Dict[str, Any]]] = {}
    for record in _iter_final_records(annotations, audits):
        gse_accession = record.get("gse_accession")
        if not isinstance(gse_accession, str) or not gse_accession:
            gse_accession = "Unknown"
        records_by_gse.setdefault(gse_accession, []).append(record)

    suggestions: List[Dict[str, Any]] = []
    for gse_accession, records in records_by_gse.items():
        for field in fields:
            if not isinstance(field, str):
                continue
            counts: Dict[str, int] = {}
            for record in records:
                value = record.get(field)
                if not isinstance(value, str):
                    continue
                counts[value] = counts.get(value, 0) + 1

            total_count = sum(counts.values())
            if total_count == 0:
                continue

            dominant_value, support_count = max(
                counts.items(),
                key=lambda item: (item[1], item[0]),
            )
            dominant_fraction = support_count / total_count
            support_fraction = _round_support_fraction(
                support_count, total_count, precision
            )

            for record in records:
                gsm_accession = record.get("gsm_accession")
                if not isinstance(gsm_accession, str) or not gsm_accession:
                    continue
                current_value = record.get(field)
                if not isinstance(current_value, str):
                    continue
                if current_value == dominant_value:
                    continue

                reason = None
                # Majority outlier rule and singleton rule (deterministic, parameterized).
                if dominant_fraction >= majority_fraction:
                    reason = _REASON_OUTLIER
                elif counts.get(current_value) == 1:
                    reason = _REASON_SINGLETON

                if reason is None:
                    continue

                suggestions.append(
                    {
                        "scope": "GSE",
                        "gse_accession": gse_accession,
                        "gsm_accession": gsm_accession,
                        "field": field,
                        "current_value": current_value,
                        "suggested_value": dominant_value,
                        "support_fraction": support_fraction,
                        "support_count": support_count,
                        "total_count": total_count,
                        "reason": reason,
                    }
                )

    suggestions.sort(
        key=lambda record: (
            record.get("gse_accession", ""),
            record.get("field", ""),
            record.get("gsm_accession", ""),
        )
    )
    return suggestions
