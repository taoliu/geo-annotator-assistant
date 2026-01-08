from __future__ import annotations

import copy
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agent.config import load_config
from agent.overrides import (
    OverrideRecord,
    apply_overrides_to_outputs,
    load_overrides,
)
from agent.run_batch import run_batch
from agent.writer import write_run_outputs
from llm.factory import StubLLMClient


def _load_stub_config() -> dict:
    cfg = load_config(str(ROOT / "config" / "example_config.yaml"))
    cfg.setdefault("parser", {})["mode"] = "stub"
    cfg.setdefault("llm", {})["transport"] = "stub"
    return cfg


def _write_jsonl(path: Path, records: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record))
            handle.write("\n")


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _parse_curation_tsv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return list(reader)


def _find_by_gsm(records: list[dict], gsm_accession: str) -> dict:
    for record in records:
        if record.get("gsm_accession") == gsm_accession:
            return record
    raise AssertionError(f"Missing record for {gsm_accession}")


def test_apply_overrides_no_changes_when_empty() -> None:
    cfg = _load_stub_config()
    annotations, audits, flagged, _ = run_batch(["GSM000001", "GSM000002"], cfg)

    before_annotations = copy.deepcopy(annotations)
    before_audits = copy.deepcopy(audits)

    apply_overrides_to_outputs({}, annotations, audits, flagged)

    assert annotations == before_annotations
    assert audits == before_audits


def test_apply_overrides_single_field_updates_outputs(tmp_path: Path) -> None:
    cfg = _load_stub_config()
    annotations, audits, flagged, _ = run_batch(["GSM000001", "GSM000002"], cfg)
    baseline = copy.deepcopy(annotations)

    overrides_path = tmp_path / "overrides.jsonl"
    _write_jsonl(
        overrides_path,
        [
            {
                "gsm_accession": "GSM000001",
                "field": "disease",
                "new_value": "Hepatocellular carcinoma",
                "reason": "Curator confirmed",
            }
        ],
    )
    overrides = load_overrides(str(overrides_path))

    apply_overrides_to_outputs(overrides, annotations, audits, flagged)

    updated = _find_by_gsm(annotations, "GSM000001")
    original = _find_by_gsm(baseline, "GSM000001")
    assert updated["disease"] == "Hepatocellular carcinoma"
    for key, value in original.items():
        if key == "disease":
            continue
        assert updated.get(key) == value

    assert _find_by_gsm(annotations, "GSM000002") == _find_by_gsm(
        baseline, "GSM000002"
    )

    audit = _find_by_gsm(audits, "GSM000001")
    applied = audit.get("human_overrides_applied")
    assert isinstance(applied, list)
    assert len(applied) == 1
    entry = applied[0]
    assert entry["gsm_accession"] == "GSM000001"
    assert entry["field"] == "disease"
    assert entry["old_value"] == original["disease"]
    assert entry["new_value"] == "Hepatocellular carcinoma"
    assert entry["reason"] == "Curator confirmed"
    assert "human_override_applied" in (audit.get("rationale") or {}).get("flags", [])

    output_paths = write_run_outputs(str(tmp_path / "out"), annotations, audits, flagged)
    tsv_rows = _parse_curation_tsv(Path(output_paths["curation"]))
    jsonl_rows = _read_jsonl(Path(output_paths["curation_jsonl"]))

    assert _find_by_gsm(tsv_rows, "GSM000001")["disease"] == "Hepatocellular carcinoma"
    assert (
        _find_by_gsm(jsonl_rows, "GSM000001")["disease"]
        == "Hepatocellular carcinoma"
    )


def test_apply_overrides_multiple_fields_are_deterministic(tmp_path: Path) -> None:
    cfg = _load_stub_config()
    annotations, audits, flagged, _ = run_batch(["GSM000001", "GSM000002"], cfg)

    overrides_path = tmp_path / "overrides.jsonl"
    _write_jsonl(
        overrides_path,
        [
            {
                "gsm_accession": "GSM000002",
                "field": "organism",
                "new_value": "Mus musculus",
            },
            {
                "gsm_accession": "GSM000001",
                "field": "tissue_type",
                "new_value": "Liver",
            },
            {
                "gsm_accession": "GSM000001",
                "field": "cell_line",
                "new_value": "HepG2",
            },
        ],
    )
    overrides = load_overrides(str(overrides_path))

    apply_overrides_to_outputs(overrides, annotations, audits, flagged)

    audit = _find_by_gsm(audits, "GSM000001")
    applied = audit.get("human_overrides_applied")
    assert isinstance(applied, list)
    assert [entry["field"] for entry in applied] == ["cell_line", "tissue_type"]

    assert _find_by_gsm(annotations, "GSM000001")["cell_line"] == "HepG2"
    assert _find_by_gsm(annotations, "GSM000001")["tissue_type"] == "Liver"
    assert _find_by_gsm(annotations, "GSM000002")["organism"] == "Mus musculus"


def test_apply_overrides_noop_is_omitted(tmp_path: Path) -> None:
    cfg = _load_stub_config()
    annotations, audits, flagged, _ = run_batch(["GSM000001"], cfg)
    baseline_disease = annotations[0]["disease"]

    overrides_path = tmp_path / "overrides.jsonl"
    _write_jsonl(
        overrides_path,
        [
            {
                "gsm_accession": "GSM000001",
                "field": "disease",
                "new_value": baseline_disease,
            }
        ],
    )
    overrides = load_overrides(str(overrides_path))

    apply_overrides_to_outputs(overrides, annotations, audits, flagged)

    audit = audits[0]
    assert "human_overrides_applied" not in audit
    assert "human_override_applied" not in (audit.get("rationale") or {}).get(
        "flags", []
    )
    assert annotations[0]["disease"] == baseline_disease


def test_overrides_do_not_increase_llm_calls(monkeypatch) -> None:
    cfg = _load_stub_config()
    client_holder: dict[str, StubLLMClient] = {}

    class CountingLLMClient(StubLLMClient):
        def __init__(self, cfg: dict | None = None) -> None:
            super().__init__(cfg)
            self.calls = 0

        def generate(self, request) -> object:
            self.calls += 1
            return super().generate(request)

    import agent.run_batch as run_batch_module

    def _fake_create_llm_client(cfg: dict) -> CountingLLMClient:
        client = CountingLLMClient(cfg)
        client_holder["client"] = client
        return client

    monkeypatch.setattr(run_batch_module, "create_llm_client", _fake_create_llm_client)

    annotations, audits, flagged, _ = run_batch_module.run_batch(["GSM000001"], cfg)
    client = client_holder["client"]
    calls_before = client.calls

    overrides = {
        ("GSM000001", "disease"): OverrideRecord(
            gsm_accession="GSM000001",
            field="disease",
            new_value="Healthy",
        )
    }
    apply_overrides_to_outputs(overrides, annotations, audits, flagged)

    assert client.calls == calls_before
