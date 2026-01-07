from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agent.writer import write_jsonl, write_run_outputs


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


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
