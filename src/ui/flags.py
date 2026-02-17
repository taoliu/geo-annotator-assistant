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

FLAG_TOOLTIP_EXACT: dict[str, str] = {
    "assay_platform_conflict": (
        "Assay platform conflicts with the inferred data type."
    ),
    "cell_line_inferred_without_evidence": (
        "Cell line was inferred without explicit evidence in the source context."
    ),
    "cell_line_is_cell_type": (
        "Cell line value appears to describe a cell type rather than a cell line."
    ),
    "cell_line_yes_invalid": "Cell line value 'Yes' is not a valid cell line name.",
    "disease_inferred_without_evidence": (
        "Disease was inferred without explicit evidence in the source context."
    ),
    "disease_unsupported": "Disease term is unsupported by the ontology.",
    "disease_contains_genotype_context": (
        "Disease label includes genotype context; informational signal."
    ),
    "disease_generalized_for_ontology": (
        "Disease term was generalized to a broader ontology-supported label."
    ),
    "disease_normalized_to_healthy": (
        "Disease value normalized to Healthy due to insufficient evidence."
    ),
    "format_unrepaired": (
        "Output format errors could not be repaired; record remains flagged."
    ),
    "healthy_disease_conflict": (
        "Disease labeled Healthy conflicts with disease cues in context."
    ),
    "invalid_json": "LLM output could not be parsed as valid JSON.",
    "missing_keys": "Required output fields were missing.",
    "extra_keys": "Output contained extra unexpected fields.",
    "word_limit_violation": "One or more field values exceeded the word limit.",
    "max_repairs_exceeded": "Repair attempts exceeded the allowed limit.",
    "ontology_index_unavailable": (
        "Ontology index was unavailable; grounding could not run."
    ),
    "ontology_partial_composite_tissue_type": (
        "Composite tissue value matched only some components; all components are required."
    ),
    "organism_context_conflict": "Organism label conflicts with context evidence.",
    "repeated_failure": "Repeated validation failures across repair attempts.",
    "single_cell_evidence_missing": (
        "Single-cell evidence missing for a single-cell data type."
    ),
    "terminal_fallback": "Terminal fallback applied for this field.",
    "tissue_type_is_cell_type": (
        "Tissue type value appears to be a cell type."
    ),
    "tissue_type_non_anatomical_placeholder": (
        "Tissue type is a non-anatomical placeholder; terminal fallback applied."
    ),
    "tissue_type_disease_label_used_as_tissue": (
        "Disease label was used as tissue type; semantic ambiguity flagged."
    ),
    "treatment_identity_leakage": (
        "Treatment field appears to contain sample identity information."
    ),
    "treatment_not_an_intervention": (
        "Treatment value is not a clear intervention."
    ),
}

_ONTOLOGY_STATUS_TOOLTIPS = {
    "NO_MATCH": "Ontology match not found for this field.",
    "LOW_CONFIDENCE": (
        "Ontology match is below confidence threshold."
    ),
    "AMBIGUOUS": "Ontology match is ambiguous between candidates.",
    "FALLBACK": "Ontology grounding fell back to a terminal policy value.",
    "TERMINAL_FALLBACK": "Ontology grounding used a terminal policy fallback.",
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


def flag_tooltip(flag_label: str) -> str:
    flag, field = _split_flag_label(flag_label)
    normalized = flag.strip()
    if not normalized:
        return "Flags are informational only."

    category = categorize_flag(normalized)
    explanation = _flag_explanation(normalized, field)
    category_label = FLAG_CATEGORY_LABELS.get(category, category)
    return (
        f"{explanation} Category: {category_label}. "
        "Flags are informational only."
    )


def primary_failure_tooltip(primary_failure: str) -> str:
    normalized = (primary_failure or "").strip()
    if not normalized:
        return ""
    category = categorize_flag(normalized)
    category_label = FLAG_CATEGORY_LABELS.get(category, category)
    return (
        "Primary failure selected deterministically based on policy severity "
        "and priority ordering. Secondary flags still apply. "
        f"Category: {category_label}."
    )


def _category_for_ontology_status(status: str) -> str:
    normalized = status.strip().upper()
    if normalized in _POLICY_ONTOLOGY_STATUSES:
        return FLAG_CATEGORY_POLICY
    if normalized in _REVIEW_ONTOLOGY_STATUSES:
        return FLAG_CATEGORY_REVIEW
    return _DEFAULT_FLAG_CATEGORY


def _flag_explanation(flag: str, field: str | None) -> str:
    if flag.startswith("ontology_status:"):
        status = flag.split(":", 1)[1].strip().upper()
        base = _ONTOLOGY_STATUS_TOOLTIPS.get(
            status, f"Ontology status is {status}."
        )
        return _with_field_prefix(base, field)

    if flag in FLAG_TOOLTIP_EXACT:
        return _with_field_prefix(FLAG_TOOLTIP_EXACT[flag], field)

    if flag.startswith("ontology_low_confidence_"):
        suffix = _suffix_field(flag, "ontology_low_confidence_")
        return _with_field_prefix(
            "Ontology match is below the acceptance threshold.",
            field or suffix,
        )
    if flag.startswith("ontology_ambiguous_"):
        suffix = _suffix_field(flag, "ontology_ambiguous_")
        return _with_field_prefix(
            "Ontology match is ambiguous between candidates.",
            field or suffix,
        )
    if flag.startswith("ontology_no_match_"):
        suffix = _suffix_field(flag, "ontology_no_match_")
        return _with_field_prefix(
            "Ontology match not found for this field.",
            field or suffix,
        )
    if flag.startswith("gse_outlier_"):
        suffix = _suffix_field(flag, "gse_outlier_")
        return _with_field_prefix(
            "Value differs from the dominant value within the GSE.",
            field or suffix,
        )
    return _with_field_prefix(
        f"Backend emitted flag '{flag}'.",
        field,
    )


def _suffix_field(flag: str, prefix: str) -> str | None:
    if not flag.startswith(prefix):
        return None
    suffix = flag[len(prefix) :]
    if suffix in CANONICAL_FIELDS:
        return suffix
    return None


def _split_flag_label(label: str) -> tuple[str, str | None]:
    raw = (label or "").strip()
    if not raw:
        return "", None
    if ": " in raw:
        left, right = raw.split(": ", 1)
        if left in CANONICAL_FIELDS:
            return right, left
    return raw, None


def _with_field_prefix(text: str, field: str | None) -> str:
    if field:
        return f"{field}: {text}"
    return text


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
    "FLAG_TOOLTIP_EXACT",
    "build_curation_flags_index",
    "build_flag_category_summary",
    "build_flag_display_groups",
    "build_flags_index",
    "build_primary_failure_index",
    "categorize_flag",
    "extract_curation_flags",
    "extract_field_flags",
    "extract_primary_failure",
    "flag_tooltip",
    "format_flag_category_summary",
    "primary_failure_tooltip",
]
