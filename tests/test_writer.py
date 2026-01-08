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
    cfg.setdefault("llm", {})["mode"] = "stub"
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
