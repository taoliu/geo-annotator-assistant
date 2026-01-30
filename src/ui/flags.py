"""Field-level flag extraction for UI highlighting."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from ui.schema import CANONICAL_FIELDS, EvidenceRecord

FLAG_CATEGORY_POLICY = "policy"
FLAG_CATEGORY_REVIEW = "review"
FLAG_CATEGORY_INFO = "info"

FLAG_CATEGORY_ORDER: tuple[str, ...] = (
    FLAG_CATEGORY_POLICY,
    FLAG_CATEGORY_REVIEW,
    FLAG_CATEGORY_INFO,
)
FLAG_CATEGORY_LABELS: dict[str, str] = {
    FLAG_CATEGORY_POLICY: "Policy / Terminal",
    FLAG_CATEGORY_REVIEW: "Ambiguity / Review Required",
    FLAG_CATEGORY_INFO: "Informational",
}
FLAG_CATEGORY_BADGES: dict[str, str] = {
    FLAG_CATEGORY_POLICY: "POLICY",
    FLAG_CATEGORY_REVIEW: "REVIEW",
    FLAG_CATEGORY_INFO: "INFO",
}
FLAG_CATEGORY_COLORS: dict[str, str] = {
    FLAG_CATEGORY_POLICY: "#fde2e2",
    FLAG_CATEGORY_REVIEW: "#fff4e5",
    FLAG_CATEGORY_INFO: "#e9f7ef",
}

_POLICY_FLAG_EXACT = {
    "format_unrepaired",
    "max_repairs_exceeded",
    "ontology_index_unavailable",
    "terminal_fallback",
}
_POLICY_FLAG_SUBSTRINGS = (
    "non_anatomical_placeholder",
    "model_identifier",
    "llm_non_answer",
)

_REVIEW_FLAG_PREFIXES = (
    "ontology_low_confidence_",
    "ontology_ambiguous_",
    "ontology_no_match_",
)
_REVIEW_FLAG_EXACT = {
    "assay_platform_conflict",
    "cell_line_inferred_without_evidence",
    "cell_line_is_cell_type",
    "cell_line_yes_invalid",
    "disease_inferred_without_evidence",
    "disease_unsupported",
    "healthy_disease_conflict",
    "invalid_json",
    "missing_keys",
    "extra_keys",
    "organism_context_conflict",
    "repeated_failure",
    "single_cell_evidence_missing",
    "tissue_type_is_cell_type",
    "tissue_type_disease_label_used_as_tissue",
    "treatment_identity_leakage",
    "treatment_not_an_intervention",
    "word_limit_violation",
}

_INFO_FLAG_PREFIXES = ("gse_outlier_",)
_INFO_FLAG_EXACT = {
    "disease_contains_genotype_context",
    "disease_generalized_for_ontology",
    "disease_normalized_to_healthy",
}
_INFO_FLAG_SUBSTRINGS = (
    "canonical",
    "generalized",
    "normalized",
    "contains_genotype",
)

_POLICY_ONTOLOGY_STATUSES = {"FALLBACK", "TERMINAL_FALLBACK"}
_REVIEW_ONTOLOGY_STATUSES = {"NO_MATCH", "LOW_CONFIDENCE", "AMBIGUOUS"}
_DEFAULT_FLAG_CATEGORY = FLAG_CATEGORY_REVIEW


def extract_field_flags(evidence_raw: dict[str, Any]) -> dict[str, list[str]]:
    """Extract per-field flags from evidence.

    Signals considered (by field):
    - evidence_by_field[<field>]["flags"] (list[str])
    - evidence_by_field[<field>]["terminal_fallback"] == True -> "terminal_fallback"
    - evidence_by_field[<field>]["ontology_status"] and != "MATCHED"
      -> "ontology_status:<STATUS>"
    """
    if not isinstance(evidence_raw, dict):
        return {}
    evidence_by_field = evidence_raw.get("evidence_by_field")
    if not isinstance(evidence_by_field, dict):
        return {}

    flags_by_field: dict[str, list[str]] = {}
    for field in CANONICAL_FIELDS:
        field_evidence = evidence_by_field.get(field)
        if not isinstance(field_evidence, dict):
            continue
        tags: list[str] = []
        raw_flags = field_evidence.get("flags")
        if isinstance(raw_flags, list):
            for flag in raw_flags:
                if isinstance(flag, str) and flag:
                    tags.append(flag)
        if field_evidence.get("terminal_fallback") is True:
            tags.append("terminal_fallback")
        ontology_status = field_evidence.get("ontology_status")
        if isinstance(ontology_status, str) and ontology_status:
            if ontology_status != "MATCHED":
                tags.append(f"ontology_status:{ontology_status}")

        if tags:
            flags_by_field[field] = _dedupe_preserve(tags)

    return flags_by_field


def build_flags_index(
    evidence_records: Iterable[EvidenceRecord],
) -> dict[tuple[str, str], dict[str, list[str]]]:
    flags_by_gsm: dict[tuple[str, str], dict[str, list[str]]] = {}
    for record in evidence_records:
        gse = record.get("gse_accession")
        gsm = record.get("gsm_accession")
        if not gse or not gsm:
            continue
        field_flags = extract_field_flags(record.get("raw", {}))
        if field_flags:
            flags_by_gsm[(gse, gsm)] = field_flags
    return flags_by_gsm


def extract_curation_flags(curation_raw: Mapping[str, Any] | None) -> list[str]:
    if not isinstance(curation_raw, Mapping):
        return []
    raw_flags = curation_raw.get("flags")
    if not isinstance(raw_flags, list):
        return []
    flags: list[str] = []
    for flag in raw_flags:
        if isinstance(flag, str) and flag:
            flags.append(flag)
    return _dedupe_preserve(flags)


def extract_primary_failure(curation_raw: Mapping[str, Any] | None) -> str:
    if not isinstance(curation_raw, Mapping):
        return ""
    value = curation_raw.get("primary_failure")
    if isinstance(value, str):
        return value.strip()
    return ""


def build_curation_flags_index(
    curation_records: Iterable[Mapping[str, Any]],
) -> dict[tuple[str, str], list[str]]:
    flags_by_gsm: dict[tuple[str, str], list[str]] = {}
    for record in curation_records:
        gse = record.get("gse_accession")
        gsm = record.get("gsm_accession")
        if not gse or not gsm:
            continue
        flags = extract_curation_flags(record.get("raw"))
        if flags:
            flags_by_gsm[(gse, gsm)] = flags
    return flags_by_gsm


def build_primary_failure_index(
    curation_records: Iterable[Mapping[str, Any]],
) -> dict[tuple[str, str], str]:
    failures_by_gsm: dict[tuple[str, str], str] = {}
    for record in curation_records:
        gse = record.get("gse_accession")
        gsm = record.get("gsm_accession")
        if not gse or not gsm:
            continue
        primary_failure = extract_primary_failure(record.get("raw"))
        if primary_failure:
            failures_by_gsm[(gse, gsm)] = primary_failure
    return failures_by_gsm


def categorize_flag(flag: str) -> str:
    normalized = (flag or "").strip()
    if not normalized:
        return _DEFAULT_FLAG_CATEGORY
    lowered = normalized.lower()
    if lowered.startswith("ontology_status:"):
        status = normalized.split(":", 1)[1].strip().upper()
        return _category_for_ontology_status(status)
    if _is_policy_flag(lowered):
        return FLAG_CATEGORY_POLICY
    if _is_info_flag(lowered):
        return FLAG_CATEGORY_INFO
    if _is_review_flag(lowered):
        return FLAG_CATEGORY_REVIEW
    return _DEFAULT_FLAG_CATEGORY


def build_flag_display_groups(
    curation_flags: Iterable[str],
    evidence_field_flags: Mapping[str, Iterable[str]] | None,
) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {key: [] for key in FLAG_CATEGORY_ORDER}
    for flag in curation_flags:
        category = categorize_flag(flag)
        grouped.setdefault(category, []).append(flag)

    if evidence_field_flags:
        for field in CANONICAL_FIELDS:
            field_flags = evidence_field_flags.get(field)
            if not field_flags:
                continue
            for flag in field_flags:
                label = f"{field}: {flag}"
                category = categorize_flag(flag)
                grouped.setdefault(category, []).append(label)
    return grouped


def build_flag_category_summary(
    curation_flags: Iterable[str],
    evidence_field_flags: Mapping[str, Iterable[str]] | None,
) -> dict[str, object]:
    counts = {key: 0 for key in FLAG_CATEGORY_ORDER}
    for flag in curation_flags:
        counts[categorize_flag(flag)] += 1
    if evidence_field_flags:
        for field in CANONICAL_FIELDS:
            field_flags = evidence_field_flags.get(field)
            if not field_flags:
                continue
            for flag in field_flags:
                counts[categorize_flag(flag)] += 1
    total = sum(counts.values())
    highest = ""
    for category in FLAG_CATEGORY_ORDER:
        if counts[category]:
            highest = category
            break
    return {"counts": counts, "highest": highest, "total": total}


def format_flag_category_summary(summary: Mapping[str, object]) -> str:
    counts = summary.get("counts")
    if not isinstance(counts, Mapping):
        return ""
    total = summary.get("total")
    if not isinstance(total, int) or total == 0:
        return ""
    policy_count = int(counts.get(FLAG_CATEGORY_POLICY, 0))
    review_count = int(counts.get(FLAG_CATEGORY_REVIEW, 0))
    info_count = int(counts.get(FLAG_CATEGORY_INFO, 0))
    highest = summary.get("highest")
    badge = ""
    if isinstance(highest, str) and highest in FLAG_CATEGORY_BADGES:
        badge = FLAG_CATEGORY_BADGES[highest] + " "
    return f"{badge}P:{policy_count} R:{review_count} I:{info_count}"


def _category_for_ontology_status(status: str) -> str:
    normalized = status.strip().upper()
    if normalized in _POLICY_ONTOLOGY_STATUSES:
        return FLAG_CATEGORY_POLICY
    if normalized in _REVIEW_ONTOLOGY_STATUSES:
        return FLAG_CATEGORY_REVIEW
    return _DEFAULT_FLAG_CATEGORY


def _is_policy_flag(flag: str) -> bool:
    if flag in _POLICY_FLAG_EXACT:
        return True
    return any(token in flag for token in _POLICY_FLAG_SUBSTRINGS)


def _is_review_flag(flag: str) -> bool:
    if flag in _REVIEW_FLAG_EXACT:
        return True
    return flag.startswith(_REVIEW_FLAG_PREFIXES)


def _is_info_flag(flag: str) -> bool:
    if flag in _INFO_FLAG_EXACT:
        return True
    if flag.startswith(_INFO_FLAG_PREFIXES):
        return True
    return any(token in flag for token in _INFO_FLAG_SUBSTRINGS)


def _dedupe_preserve(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if item not in seen:
            ordered.append(item)
            seen.add(item)
    return ordered


__all__ = [
    "FLAG_CATEGORY_BADGES",
    "FLAG_CATEGORY_COLORS",
    "FLAG_CATEGORY_INFO",
    "FLAG_CATEGORY_LABELS",
    "FLAG_CATEGORY_ORDER",
    "FLAG_CATEGORY_POLICY",
    "FLAG_CATEGORY_REVIEW",
    "build_curation_flags_index",
    "build_flag_category_summary",
    "build_flag_display_groups",
    "build_flags_index",
    "build_primary_failure_index",
    "categorize_flag",
    "extract_curation_flags",
    "extract_field_flags",
    "extract_primary_failure",
    "format_flag_category_summary",
]
