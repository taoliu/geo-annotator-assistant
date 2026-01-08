from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agent.config import load_config
from agent.run_batch import run_batch
from agent.writer import write_jsonl, write_run_outputs


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _load_stub_config() -> dict:
    cfg = load_config(str(ROOT / "config" / "example_config.yaml"))
    cfg.setdefault("parser", {})["mode"] = "stub"
    cfg.setdefault("llm", {})["transport"] = "stub"
    return cfg


def _parse_curation_tsv(path: Path) -> tuple[list[str], list[dict]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        header = reader.fieldnames or []
        rows = list(reader)
    return header, rows


def _coerce_tsv_value(column: str, value: str) -> object:
    if column in {"terminal_fallback_fields", "flags"}:
        return json.loads(value) if value else []
    if column == "attempts_by_field":
        return json.loads(value) if value else {}
    if column == "n_llm_calls":
        return int(value) if value else 0
    return value


def _normalize_tsv_row(row: dict) -> dict:
    return {col: _coerce_tsv_value(col, row.get(col, "")) for col in row}


_EVIDENCE_FIELDS = [
    "data_type",
    "organism",
    "tissue_type",
    "cell_line",
    "disease",
    "treatment",
]

_FIELD_FLAG_ALIASES = {
    "data_type": {"assay_platform_conflict", "single_cell_evidence_missing"},
}


def _normalize_flags(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [flag for flag in value if isinstance(flag, str)]


def _collect_audit_flags(audit: dict) -> list[str]:
    flags: list[str] = []
    rationale = audit.get("rationale")
    if not isinstance(rationale, dict):
        rationale = {}

    for flag in _normalize_flags(rationale.get("flags")):
        if flag not in flags:
            flags.append(flag)
    for flag in _normalize_flags(audit.get("flags")):
        if flag not in flags:
            flags.append(flag)

    outlier_keys = sorted(
        key for key, value in audit.items() if key.startswith("gse_outlier_") and value
    )
    for key in outlier_keys:
        if key not in flags:
            flags.append(key)

    return flags


def _flag_applies_to_field(flag: str, field: str) -> bool:
    if flag in _FIELD_FLAG_ALIASES.get(field, set()):
        return True
    if flag == f"gse_outlier_{field}":
        return True
    if flag.startswith(f"{field}_") or flag.endswith(f"_{field}"):
        return True
    if f"_{field}_" in flag:
        return True
    return False


def _build_expected_evidence(annotation: dict, audit: dict) -> dict:
    final_output = audit.get("final_output")
    if not isinstance(final_output, dict):
        final_output = annotation if isinstance(annotation, dict) else {}
    rationale = audit.get("rationale")
    if not isinstance(rationale, dict):
        rationale = {}
    attempts_by_field = rationale.get("attempts_by_field")
    if not isinstance(attempts_by_field, dict):
        attempts_by_field = {}
    terminal_fallback_fields = rationale.get("terminal_fallback_fields")
    if not isinstance(terminal_fallback_fields, list):
        terminal_fallback_fields = []
    statuses = rationale.get("ontology_status_by_field")
    if not isinstance(statuses, dict):
        statuses = {}

    flags = _collect_audit_flags(audit)
    evidence_by_field: dict[str, dict] = {}
    for field in _EVIDENCE_FIELDS:
        attempts_value = attempts_by_field.get(field, 0)
        try:
            attempts = int(attempts_value)
        except (TypeError, ValueError):
            attempts = 0
        ontology_status = statuses.get(field)
        if not isinstance(ontology_status, str):
            ontology_status = ""

        evidence_by_field[field] = {
            "attempts": attempts,
            "terminal_fallback": field in terminal_fallback_fields,
            "ontology_status": ontology_status,
            "flags": [flag for flag in flags if _flag_applies_to_field(flag, field)],
        }

    return {
        "gse_accession": audit.get("gse_accession")
        or final_output.get("gse_accession")
        or "",
        "gsm_accession": audit.get("gsm_accession")
        or final_output.get("gsm_accession")
        or "",
        "evidence_by_field": evidence_by_field,
    }


def test_write_run_outputs_creates_jsonl(tmp_path: Path) -> None:
    annotations = [{"a": 1}, {"a": 2, "b": "x"}]
    audits = [{"event": "start"}, {"event": "end"}]
    flagged = [{"flag": True}]

    output = write_run_outputs(str(tmp_path), annotations, audits, flagged)

    expected = {
        "annotations": annotations,
        "audit": audits,
        "flagged": flagged,
    }
    for key, records in expected.items():
        path = Path(output[key])
        assert path.exists()
        parsed = _read_jsonl(path)
        assert len(parsed) == len(records)
        assert parsed == records

    curation_path = Path(output["curation"])
    assert curation_path.exists()
    lines = curation_path.read_text(encoding="utf-8").splitlines()
    assert lines[0].startswith("gse_accession\tgsm_accession\tfinal_decision")
    assert len(lines) == len(audits) + 1

    curation_jsonl_path = Path(output["curation_jsonl"])
    assert curation_jsonl_path.exists()
    assert len(curation_jsonl_path.read_text(encoding="utf-8").splitlines()) == len(
        audits
    )

    evidence_path = Path(output["evidence"])
    assert evidence_path.exists()
    assert len(evidence_path.read_text(encoding="utf-8").splitlines()) == len(audits)


def test_curation_jsonl_matches_tsv(tmp_path: Path) -> None:
    cfg = _load_stub_config()
    annotations, audits, flagged, _ = run_batch(["GSM000001", "GSM000002"], cfg)

    output = write_run_outputs(str(tmp_path), annotations, audits, flagged)

    tsv_header, tsv_rows = _parse_curation_tsv(Path(output["curation"]))
    jsonl_rows = _read_jsonl(Path(output["curation_jsonl"]))

    assert len(tsv_rows) == len(jsonl_rows)
    assert len(tsv_header) == 16
    for tsv_row, json_row in zip(tsv_rows, jsonl_rows):
        normalized_row = _normalize_tsv_row(tsv_row)
        assert normalized_row == json_row


def test_curation_jsonl_schema_matches_tsv(tmp_path: Path) -> None:
    cfg = _load_stub_config()
    annotations, audits, flagged, _ = run_batch(["GSM000001", "GSM000002"], cfg)

    output = write_run_outputs(str(tmp_path), annotations, audits, flagged)

    tsv_header, _ = _parse_curation_tsv(Path(output["curation"]))
    jsonl_rows = _read_jsonl(Path(output["curation_jsonl"]))

    assert len(tsv_header) == 16
    for record in jsonl_rows:
        assert list(record.keys()) == tsv_header


def test_curation_jsonl_deterministic(tmp_path: Path) -> None:
    first_dir = tmp_path / "run1"
    second_dir = tmp_path / "run2"

    cfg = _load_stub_config()
    annotations, audits, flagged, _ = run_batch(["GSM000001", "GSM000002"], cfg)
    output_first = write_run_outputs(str(first_dir), annotations, audits, flagged)

    cfg = _load_stub_config()
    annotations, audits, flagged, _ = run_batch(["GSM000001", "GSM000002"], cfg)
    output_second = write_run_outputs(str(second_dir), annotations, audits, flagged)

    first_bytes = Path(output_first["curation_jsonl"]).read_bytes()
    second_bytes = Path(output_second["curation_jsonl"]).read_bytes()

    assert first_bytes == second_bytes


def test_evidence_jsonl_schema_defaults(tmp_path: Path) -> None:
    annotations = [{"gse_accession": "GSE1", "gsm_accession": "GSM1"}]
    audits = [{"gse_accession": "GSE1", "gsm_accession": "GSM1"}]

    output = write_run_outputs(str(tmp_path), annotations, audits, [])

    evidence = _read_jsonl(Path(output["evidence"]))
    assert len(evidence) == 1
    record = evidence[0]
    assert list(record.keys()) == ["gse_accession", "gsm_accession", "evidence_by_field"]
    assert list(record["evidence_by_field"].keys()) == _EVIDENCE_FIELDS

    for field in _EVIDENCE_FIELDS:
        field_info = record["evidence_by_field"][field]
        assert field_info["attempts"] == 0
        assert field_info["terminal_fallback"] is False
        assert field_info["ontology_status"] == ""
        assert field_info["flags"] == []


def test_evidence_jsonl_matches_audit(tmp_path: Path) -> None:
    cfg = _load_stub_config()
    annotations, audits, flagged, _ = run_batch(["GSM000001", "GSM000002"], cfg)

    output = write_run_outputs(str(tmp_path), annotations, audits, flagged)

    evidence_rows = _read_jsonl(Path(output["evidence"]))
    assert len(evidence_rows) == len(audits)
    for annotation, audit, evidence in zip(annotations, audits, evidence_rows):
        expected = _build_expected_evidence(annotation, audit)
        assert evidence == expected


def test_evidence_jsonl_deterministic(tmp_path: Path) -> None:
    first_dir = tmp_path / "run1"
    second_dir = tmp_path / "run2"

    cfg = _load_stub_config()
    annotations, audits, flagged, _ = run_batch(["GSM000001", "GSM000002"], cfg)
    output_first = write_run_outputs(str(first_dir), annotations, audits, flagged)

    cfg = _load_stub_config()
    annotations, audits, flagged, _ = run_batch(["GSM000001", "GSM000002"], cfg)
    output_second = write_run_outputs(str(second_dir), annotations, audits, flagged)

    first_bytes = Path(output_first["evidence"]).read_bytes()
    second_bytes = Path(output_second["evidence"]).read_bytes()

    assert first_bytes == second_bytes


def test_write_jsonl_overwrites_atomically(tmp_path: Path) -> None:
    path = tmp_path / "data.jsonl"
    write_jsonl(str(path), [{"a": 1}])
    write_jsonl(str(path), [{"b": 2}, {"c": 3}])

    parsed = _read_jsonl(path)
    assert parsed == [{"b": 2}, {"c": 3}]


def test_write_jsonl_raises_on_unserializable(tmp_path: Path) -> None:
    path = tmp_path / "bad.jsonl"
    with pytest.raises(ValueError, match="not JSON-serializable"):
        write_jsonl(str(path), [{"bad": {1, 2}}])
