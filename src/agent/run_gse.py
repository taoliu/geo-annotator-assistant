"""GSE-mode runner for JSONL GSM context records."""

from __future__ import annotations

from typing import Any, Dict, List

from agent.gse_postpass import (
    apply_gse_consistency_postpass,
    apply_gse_field_values_summary,
)
from agent.run_single import run_single_from_context_record
from llm.factory import create_llm_client
from ingest.read_context_jsonl import iter_gsm_contexts
from ingest.soft_to_context_jsonl import soft_to_context_jsonl

_REQUIRED_KEYS: List[str] = [
    "gse_accession",
    "gsm_accession",
    "data_type",
    "organism",
    "tissue_type",
    "cell_line",
    "disease",
    "treatment",
]

_PLACEHOLDERS: Dict[str, str] = {
    "gse_accession": "Unknown",
    "data_type": "Unknown",
    "organism": "Unknown",
    "tissue_type": "Unknown",
    "cell_line": "No",
    "disease": "Healthy",
    "treatment": "None",
}


def _build_failure_annotation(record: dict) -> Dict[str, str]:
    annotation = {key: _PLACEHOLDERS.get(key, "Unknown") for key in _REQUIRED_KEYS}
    annotation["gsm_accession"] = record.get("gsm_accession", "Unknown")
    annotation["gse_accession"] = record.get("gse_accession", "Unknown")
    return annotation


def _build_failure_audit(record: dict, error_message: str) -> Dict[str, str]:
    message = error_message or "Unknown error"
    return {
        "gsm_accession": record.get("gsm_accession", "Unknown"),
        "gse_accession": record.get("gse_accession", "Unknown"),
        "error": message,
        "final_decision": "FLAGGED",
        "rationale": {
            "final_decision": "FLAGGED",
            "primary_failure": None,
            "terminal_fallback_fields": [],
            "n_llm_calls": 0,
            "attempts_by_field": {},
            "ontology_status_by_field": {},
            "flags": [],
        },
    }


def run_gse_from_jsonl(
    jsonl_path: str,
    cfg: dict,
) -> tuple[list[dict], list[dict], list[dict], dict, dict | None, dict | None]:
    annotations: List[Dict[str, Any]] = []
    audits: List[Dict[str, Any]] = []
    flagged: List[Dict[str, Any]] = []
    n_flagged = 0
    llm_client = None
    reuse_logged = False
    llm_cfg = cfg.get("llm", {}) if isinstance(cfg.get("llm"), dict) else {}
    llm_transport = llm_cfg.get("transport") or llm_cfg.get("mode", "stub")

    for record in iter_gsm_contexts(jsonl_path):
        try:
            if llm_client is None:
                llm_client = create_llm_client(llm_cfg)
            elif not reuse_logged and llm_transport in {"local_transformers", "transformers"}:
                print("[LLM] Reusing existing model instance")
                reuse_logged = True

            annotation, audit, is_flagged = run_single_from_context_record(
                record,
                cfg,
                llm_client=llm_client,
            )
        except Exception as exc:
            annotation = _build_failure_annotation(record)
            audit = _build_failure_audit(record, str(exc))
            is_flagged = True

        annotations.append(annotation)
        audits.append(audit)
        if is_flagged:
            flagged.append(annotation)
            n_flagged += 1

    summary = {
        "n_total": len(annotations),
        "n_accepted": len(annotations) - n_flagged,
        "n_flagged": n_flagged,
    }
    gse_report = apply_gse_consistency_postpass(annotations, audits, cfg)
    gse_values = apply_gse_field_values_summary(annotations, cfg)
    return annotations, audits, flagged, summary, gse_report, gse_values


def run_gse_from_accession(
    gse_accession: str,
    cfg: dict,
    work_dir: str,
) -> tuple[list[dict], list[dict], list[dict], dict, dict | None, dict | None]:
    paths_cfg = cfg.get("paths") if isinstance(cfg.get("paths"), dict) else {}
    jsonl_path = soft_to_context_jsonl(
        gse_accession=gse_accession,
        work_dir=work_dir,
        soft_cache_dir=paths_cfg.get("soft_cache_dir"),
    )
    return run_gse_from_jsonl(jsonl_path, cfg)


def run_gse_from_soft_file(
    soft_path: str,
    cfg: dict,
    work_dir: str,
) -> tuple[list[dict], list[dict], list[dict], dict, dict | None, dict | None]:
    jsonl_path = soft_to_context_jsonl(
        soft_path=soft_path,
        work_dir=work_dir,
    )
    return run_gse_from_jsonl(jsonl_path, cfg)
