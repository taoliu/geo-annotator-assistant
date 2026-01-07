"""JSONL output writer with atomic writes."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional


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

    write_jsonl(str(annotations_path), annotations)
    write_jsonl(str(audit_path), audits)
    write_jsonl(str(flagged_path), flagged)

    output_paths = {
        "annotations": str(annotations_path),
        "audit": str(audit_path),
        "flagged": str(flagged_path),
    }

    if extra_json:
        for name, payload in extra_json.items():
            extra_path = output_path / name
            write_json(str(extra_path), payload)
            output_paths[name] = str(extra_path)

    return output_paths
