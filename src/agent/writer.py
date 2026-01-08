"""JSONL output writer with atomic writes."""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

_CURATION_COLUMNS = [
    "gse_accession",
    "gsm_accession",
    "final_decision",
    "data_type",
    "organism",
    "tissue_type",
    "cell_line",
    "disease",
    "treatment",
    "primary_failure",
    "terminal_fallback_fields",
    "n_llm_calls",
    "attempts_by_field",
    "ontology_status_tissue_type",
    "ontology_status_disease",
    "flags",
]


def write_jsonl(path: str, records: List[Dict[str, Any]]) -> None:
    tmp_path = f"{os.fspath(path)}.tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8", newline="\n") as handle:
            for idx, record in enumerate(records):
                try:
                    line = json.dumps(record, ensure_ascii=False)
                except (TypeError, ValueError) as exc:
                    raise ValueError(
                        f"Record at index {idx} is not JSON-serializable: {exc}"
                    ) from exc
                handle.write(line)
                handle.write("\n")
        os.replace(tmp_path, os.fspath(path))
    except Exception:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
        raise


def write_json(path: str, payload: Dict[str, Any]) -> None:
    tmp_path = f"{os.fspath(path)}.tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(tmp_path, os.fspath(path))
    except Exception:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
        raise


def _stringify_tsv_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return str(value)


def _build_curation_row(
    annotation: Dict[str, Any],
    audit: Dict[str, Any],
) -> Dict[str, Any]:
    final_output = audit.get("final_output")
    if not isinstance(final_output, dict):
        final_output = annotation if isinstance(annotation, dict) else {}
    rationale = audit.get("rationale")
    if not isinstance(rationale, dict):
        rationale = {}
    statuses = rationale.get("ontology_status_by_field")
    if not isinstance(statuses, dict):
        statuses = {}

    flags = rationale.get("flags")
    if not isinstance(flags, list):
        flags = []
    for key, value in audit.items():
        if key.startswith("gse_outlier_") and value:
            if key not in flags:
                flags.append(key)

    return {
        "gse_accession": audit.get("gse_accession")
        or final_output.get("gse_accession")
        or "",
        "gsm_accession": audit.get("gsm_accession")
        or final_output.get("gsm_accession")
        or "",
        "final_decision": audit.get("final_decision") or "",
        "data_type": final_output.get("data_type") or "",
        "organism": final_output.get("organism") or "",
        "tissue_type": final_output.get("tissue_type") or "",
        "cell_line": final_output.get("cell_line") or "",
        "disease": final_output.get("disease") or "",
        "treatment": final_output.get("treatment") or "",
        "primary_failure": rationale.get("primary_failure") or "",
        "terminal_fallback_fields": rationale.get("terminal_fallback_fields", []),
        "n_llm_calls": rationale.get("n_llm_calls", 0),
        "attempts_by_field": rationale.get("attempts_by_field", {}),
        "ontology_status_tissue_type": statuses.get("tissue_type") or "",
        "ontology_status_disease": statuses.get("disease") or "",
        "flags": flags,
    }


def _iter_curation_records(
    annotations: List[Dict[str, Any]],
    audits: List[Dict[str, Any]],
) -> Iterator[Dict[str, Any]]:
    total_rows = max(len(annotations), len(audits))
    for idx in range(total_rows):
        annotation = annotations[idx] if idx < len(annotations) else {}
        audit = audits[idx] if idx < len(audits) else {}
        row = _build_curation_row(annotation, audit)
        yield {col: row.get(col) for col in _CURATION_COLUMNS}


def write_curation_jsonl(
    path: str,
    annotations: List[Dict[str, Any]],
    audits: List[Dict[str, Any]],
) -> None:
    records = list(_iter_curation_records(annotations, audits))
    write_jsonl(path, records)


def write_curation_tsv(
    path: str,
    annotations: List[Dict[str, Any]],
    audits: List[Dict[str, Any]],
) -> None:
    tmp_path = f"{os.fspath(path)}.tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8", newline="\n") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=_CURATION_COLUMNS,
                delimiter="\t",
            )
            writer.writeheader()
            for row in _iter_curation_records(annotations, audits):
                writer.writerow(
                    {col: _stringify_tsv_value(row.get(col)) for col in _CURATION_COLUMNS}
                )
        os.replace(tmp_path, os.fspath(path))
    except Exception:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
        raise


def write_run_outputs(
    output_dir: str,
    annotations: List[Dict[str, Any]],
    audits: List[Dict[str, Any]],
    flagged: List[Dict[str, Any]],
    extra_json: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Dict[str, str]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    annotations_path = output_path / "annotations.jsonl"
    audit_path = output_path / "audit.jsonl"
    flagged_path = output_path / "flagged.jsonl"
    curation_path = output_path / "curation.tsv"
    curation_jsonl_path = output_path / "curation.jsonl"

    write_jsonl(str(annotations_path), annotations)
    write_jsonl(str(audit_path), audits)
    write_jsonl(str(flagged_path), flagged)
    write_curation_jsonl(str(curation_jsonl_path), annotations, audits)
    write_curation_tsv(str(curation_path), annotations, audits)

    output_paths = {
        "annotations": str(annotations_path),
        "audit": str(audit_path),
        "flagged": str(flagged_path),
        "curation": str(curation_path),
        "curation_jsonl": str(curation_jsonl_path),
    }

    if extra_json:
        for name, payload in extra_json.items():
            extra_path = output_path / name
            write_json(str(extra_path), payload)
            output_paths[name] = str(extra_path)

    return output_paths
