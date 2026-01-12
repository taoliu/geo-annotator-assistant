"""Standardize curator-provided GSM annotations against ontology grounders."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Iterator, List, Tuple

from agent.ontology_canonicalization import apply_terminal_exact_canonicalization_and_lock
from agent.state import PipelineState
from agent.writer import write_jsonl
from validator.ontology_validator import ground_all_fields

REQUIRED_GSM_FIELDS = (
    "gse_accession",
    "gsm_accession",
    "data_type",
    "organism",
    "tissue_type",
    "cell_line",
    "disease",
    "treatment",
)

GROUNDED_FIELDS = (
    "data_type",
    "tissue_type",
    "cell_line",
    "disease",
)


def _canonicalize_enabled(
    config: dict[str, Any],
    override: bool | None,
) -> bool:
    if override is not None:
        return bool(override)
    if not isinstance(config, dict):
        return False
    rag_cfg = config.get("rag") if isinstance(config.get("rag"), dict) else {}
    ontology_cfg = rag_cfg.get("ontology") if isinstance(rag_cfg.get("ontology"), dict) else {}
    return bool(ontology_cfg.get("canonicalize_terminal_exact_labels", False))


def _canonicalize_config(enabled: bool) -> dict[str, Any]:
    return {
        "rag": {
            "ontology": {
                "canonicalize_terminal_exact_labels": enabled,
                "lock_terminal_exact_fields": False,
            }
        }
    }


def _iter_jsonl_records(path: str) -> Iterator[tuple[int, dict[str, Any]]]:
    path_obj = Path(path)
    with path_obj.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                record = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"{path_obj}:{line_number}: invalid JSON ({exc.msg})"
                ) from exc
            if not isinstance(record, dict):
                raise ValueError(f"{path_obj}:{line_number}: expected a JSON object")
            yield line_number, record


def _normalize_record(record: dict[str, Any], error_prefix: str) -> dict[str, str]:
    normalized: dict[str, str] = {}
    for key in REQUIRED_GSM_FIELDS:
        if key not in record:
            raise ValueError(f"{error_prefix}: missing key '{key}'")
        value = record.get(key)
        if not isinstance(value, str):
            raise ValueError(f"{error_prefix}: key '{key}' must be a string")
        normalized[key] = value
    return normalized


def _match_attr(match: Any, attr: str) -> Any:
    if match is None:
        return None
    if isinstance(match, dict):
        return match.get(attr)
    return getattr(match, attr, None)


def _build_audit_record(
    record: dict[str, str],
    matches: dict[str, Any],
    canonicalizations: dict[str, dict[str, Any]],
    locked_fields: dict[str, dict[str, Any]],
    fields_to_ground: set[str],
) -> dict[str, Any]:
    grounding: dict[str, dict[str, Any]] = {}
    for field in GROUNDED_FIELDS:
        if field in fields_to_ground:
            match = matches.get(field)
            status = _match_attr(match, "status")
            score = _match_attr(match, "score")
            match_type = _match_attr(match, "match_type")
            ontology = _match_attr(match, "ontology")
            canonical_label = canonicalizations.get(field, {}).get("canonical_value")
            locked = field in locked_fields
        else:
            match = matches.get(field)
            status = "SKIPPED"
            score = None
            match_type = None
            ontology = _match_attr(match, "ontology")
            canonical_label = None
            locked = False
        grounding[field] = {
            "status": status,
            "score": score,
            "match_type": match_type,
            "ontology": ontology,
            "canonical_label_used": canonical_label,
            "locked": locked,
        }
    return {
        "gse_accession": record["gse_accession"],
        "gsm_accession": record["gsm_accession"],
        "grounding": grounding,
    }


def standardize_terms_records(
    records: Iterable[dict[str, Any]],
    config: dict[str, Any],
    *,
    fields: Iterable[str] | None = None,
    canonicalize: bool | None = None,
) -> Tuple[List[dict[str, str]], List[dict[str, Any]]]:
    field_list = list(fields) if fields else list(GROUNDED_FIELDS)
    fields_to_ground = set(field_list)
    canonicalize_enabled = _canonicalize_enabled(config, canonicalize)
    rag_cfg = config.get("rag") if isinstance(config.get("rag"), dict) else {}

    outputs: List[dict[str, str]] = []
    audits: List[dict[str, Any]] = []

    for idx, record in enumerate(records, start=1):
        normalized = _normalize_record(record, f"Record {idx}")
        grounding_input = {
            field: normalized[field] if field in fields_to_ground else ""
            for field in GROUNDED_FIELDS
        }
        matches, _ = ground_all_fields(grounding_input, "", rag_cfg)

        output_record = {field: normalized[field] for field in REQUIRED_GSM_FIELDS}
        canonicalizations: dict[str, dict[str, Any]] = {}
        locked_fields: dict[str, dict[str, Any]] = {}

        if canonicalize_enabled:
            state = PipelineState(
                gsm_accession=normalized["gsm_accession"],
                gse_accession=normalized["gse_accession"],
                final_output=dict(output_record),
                ontology_matches=matches,
            )
            apply_terminal_exact_canonicalization_and_lock(
                state,
                _canonicalize_config(canonicalize_enabled),
            )
            if state.final_output:
                output_record = dict(state.final_output)
            canonicalizations = dict(state.canonicalizations)
            locked_fields = dict(state.locked_fields)

        outputs.append({field: output_record[field] for field in REQUIRED_GSM_FIELDS})
        audits.append(
            _build_audit_record(
                normalized,
                matches,
                canonicalizations,
                locked_fields,
                fields_to_ground,
            )
        )

    return outputs, audits


def standardize_terms_jsonl(
    input_path: str,
    output_path: str,
    audit_path: str,
    config: dict[str, Any],
    *,
    fields: Iterable[str] | None = None,
    canonicalize: bool | None = None,
) -> Tuple[List[dict[str, str]], List[dict[str, Any]]]:
    records: List[dict[str, Any]] = []
    for line_number, record in _iter_jsonl_records(input_path):
        normalized = _normalize_record(record, f"{input_path}:{line_number}")
        normalized.update(
            {
                key: value
                for key, value in record.items()
                if key not in normalized
            }
        )
        records.append(normalized)

    outputs, audits = standardize_terms_records(
        records,
        config,
        fields=fields,
        canonicalize=canonicalize,
    )
    write_jsonl(output_path, outputs)
    write_jsonl(audit_path, audits)
    return outputs, audits
