"""Batch runner for GSM accessions."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from agent.run_single import run_single_gsm
from llm.factory import create_llm_client

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


def _build_failure_annotation(gsm_accession: str) -> Dict[str, str]:
    record = {key: _PLACEHOLDERS.get(key, "Unknown") for key in _REQUIRED_KEYS}
    record["gsm_accession"] = gsm_accession
    return record


def _build_failure_audit(gsm_accession: str, error_message: str) -> Dict[str, str]:
    message = error_message or "Unknown error"
    return {
        "gsm_accession": gsm_accession,
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


def run_batch(
    gsms: list[str],
    cfg: dict,
) -> tuple[list[dict], list[dict], list[dict], dict]:
    annotations: List[Dict[str, Any]] = []
    audits: List[Dict[str, Any]] = []
    flagged: List[Dict[str, Any]] = []
    n_flagged = 0

    llm_client = None
    reuse_logged = False
    llm_cfg = cfg.get("llm", {}) if isinstance(cfg.get("llm"), dict) else {}
    llm_mode = llm_cfg.get("mode", "stub")

    for gsm_accession in gsms:
        try:
            if llm_client is None:
                llm_client = create_llm_client(llm_cfg)
            elif not reuse_logged and llm_mode in {"local_transformers", "transformers"}:
                print("[LLM] Reusing existing model instance")
                reuse_logged = True

            annotation, audit, is_flagged = run_single_gsm(
                gsm_accession,
                cfg,
                llm_client=llm_client,
            )
        except Exception as exc:
            annotation = _build_failure_annotation(gsm_accession)
            audit = _build_failure_audit(gsm_accession, str(exc))
            is_flagged = True

        annotations.append(annotation)
        audits.append(audit)
        if is_flagged:
            flagged.append(annotation)
            n_flagged += 1

    summary = {
        "n_total": len(gsms),
        "n_accepted": len(gsms) - n_flagged,
        "n_flagged": n_flagged,
    }
    return annotations, audits, flagged, summary
