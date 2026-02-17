from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agent.config import load_config
from agent.run_single import run_single_from_context_record
from agent.writer import write_run_outputs
import agent.run_single as run_single_module
import validator.ontology_validator as ontology_validator
from llm.base import LLMRequest, LLMResult, compute_request_fingerprint
from validator.failure_codes import (
    ONTOLOGY_LOW_CONFIDENCE_TISSUE_TYPE,
    ONTOLOGY_PARTIAL_COMPOSITE_TISSUE_TYPE,
)
from validator.ontology_match import OntologyMatch


class FakeLLMClient:
    def __init__(self, outputs: list[str]) -> None:
        self._outputs = list(outputs)

    def generate(self, request: LLMRequest) -> LLMResult:
        if not self._outputs:
            raise AssertionError("FakeLLMClient has no remaining outputs.")
        text = self._outputs.pop(0)
        return LLMResult(
            text=text,
            request_id=request.request_id,
            usage=None,
            transport_meta={"provider": "fake"},
            request_fingerprint=compute_request_fingerprint(request),
        )


def _load_stub_config() -> dict:
    cfg = load_config(str(ROOT / "config" / "example_config.yaml"))
    cfg.setdefault("llm", {})["transport"] = "stub"
    cfg.setdefault("limits", {})
    return cfg


def _make_output(**overrides: str) -> str:
    base = {
        "gse_accession": "GSE184398",
        "gsm_accession": "GSM5585963",
        "data_type": "RNA-seq",
        "organism": "Homo sapiens",
        "tissue_type": "Colon & Rectum",
        "cell_line": "No",
        "disease": "Healthy",
        "treatment": "None",
    }
    base.update(overrides)
    return json.dumps(base, ensure_ascii=True)


def _match_exact(
    raw_value: str,
    label: str,
    term_id: str,
    *,
    match_type: str = "label_norm_exact",
    matched_via: str = "label_norm",
) -> OntologyMatch:
    return OntologyMatch(
        field="tissue_type",
        raw_value=raw_value,
        ontology="Uberon Ontology",
        status="MATCHED",
        matched_term_id=term_id,
        matched_label=label,
        matched_source="Uberon Ontology",
        match_type=match_type,
        score=1.0,
        alternates=[],
        matched_via=matched_via,
    )


def _match_low_confidence(raw_value: str, label: str) -> OntologyMatch:
    return OntologyMatch(
        field="tissue_type",
        raw_value=raw_value,
        ontology="Uberon Ontology",
        status="LOW_CONFIDENCE",
        matched_term_id=None,
        matched_label=None,
        matched_source=None,
        match_type="jaccard",
        score=0.61,
        alternates=[
            {
                "term_id": "UBERON:0000000",
                "label": label,
                "source": "Uberon Ontology",
                "confidence": 0.61,
            }
        ],
    )


def _match_no_match(raw_value: str) -> OntologyMatch:
    return OntologyMatch(
        field="tissue_type",
        raw_value=raw_value,
        ontology="Uberon Ontology",
        status="NO_MATCH",
        matched_term_id=None,
        matched_label=None,
        matched_source=None,
        match_type="none",
        score=0.0,
        alternates=[],
    )


def test_composite_tissue_all_components_exact_produces_canonical_joined_output(
    monkeypatch,
) -> None:
    cfg = _load_stub_config()
    record = {
        "gsm_accession": "GSM5585963",
        "gse_accession": "GSE184398",
        "context_text": "Colon & Rectum tissues.",
    }
    outputs = [_make_output(tissue_type="Colon & Rectum")]
    fake_client = FakeLLMClient(outputs)
    monkeypatch.setattr(run_single_module, "create_llm_client", lambda _cfg: fake_client)

    calls: list[str] = []

    def _ground_tissue(raw_value: str, _context: str, _cfg: dict) -> OntologyMatch:
        calls.append(raw_value)
        if raw_value == "Colon & Rectum":
            return _match_low_confidence(raw_value, "colon")
        if raw_value == "Colon":
            return _match_exact(raw_value, "colon", "UBERON:0001155")
        if raw_value == "Rectum":
            return _match_exact(raw_value, "rectum", "UBERON:0001052")
        return _match_no_match(raw_value)

    monkeypatch.setattr(
        ontology_validator,
        "_tissue_type_grounder",
        SimpleNamespace(ground_tissue_type=_ground_tissue),
    )

    output, audit_record, flagged = run_single_from_context_record(record, cfg)

    assert flagged is False
    assert audit_record["final_decision"] == "ACCEPT"
    assert output["tissue_type"] == "colon & rectum"
    assert audit_record["rationale"]["ontology_status_by_field"]["tissue_type"] == "MATCHED"
    assert audit_record["attempts_by_field"].get("tissue_type", 0) == 0
    assert all(entry.get("field") != "tissue_type" for entry in audit_record["repair_history"])
    tissue_match = audit_record["validation"]["ontology_matches"]["tissue_type"]
    assert tissue_match["selection_rule"] == "all_components_required_v1"
    composite = tissue_match["composite_resolution"]
    assert composite["fragments"] == ["Colon", "Rectum"]
    assert composite["final_joined_label"] == "colon & rectum"
    assert calls == ["Colon & Rectum", "Colon", "Rectum"]


def test_composite_tissue_partial_match_escalates_without_repair_attempts(
    monkeypatch,
    tmp_path: Path,
) -> None:
    cfg = _load_stub_config()
    record = {
        "gsm_accession": "GSM5585964",
        "gse_accession": "GSE184398",
        "context_text": "Colon and unmatched compartment.",
    }
    outputs = [_make_output(gsm_accession="GSM5585964", tissue_type="Colon & Mystery Tissue")]
    fake_client = FakeLLMClient(outputs)
    monkeypatch.setattr(run_single_module, "create_llm_client", lambda _cfg: fake_client)

    def _ground_tissue(raw_value: str, _context: str, _cfg: dict) -> OntologyMatch:
        if raw_value == "Colon & Mystery Tissue":
            return _match_low_confidence(raw_value, "colon")
        if raw_value == "Colon":
            return _match_exact(raw_value, "colon", "UBERON:0001155")
        if raw_value == "Mystery Tissue":
            return _match_no_match(raw_value)
        return _match_no_match(raw_value)

    monkeypatch.setattr(
        ontology_validator,
        "_tissue_type_grounder",
        SimpleNamespace(ground_tissue_type=_ground_tissue),
    )

    output, audit_record, flagged = run_single_from_context_record(record, cfg)

    assert flagged is True
    assert audit_record["final_decision"] == "FLAGGED"
    assert output["tissue_type"] == "Colon & Mystery Tissue"
    assert audit_record["rationale"]["primary_failure"] == ONTOLOGY_PARTIAL_COMPOSITE_TISSUE_TYPE
    assert ONTOLOGY_PARTIAL_COMPOSITE_TISSUE_TYPE in audit_record["flags"]
    assert (
        audit_record["validation"]["ontology_failures"]["tissue_type"]
        == ONTOLOGY_PARTIAL_COMPOSITE_TISSUE_TYPE
    )
    assert audit_record["rationale"]["ontology_status_by_field"]["tissue_type"] == "LOW_CONFIDENCE"
    assert audit_record["attempts_by_field"].get("tissue_type", 0) == 0
    assert all(entry.get("field") != "tissue_type" for entry in audit_record["repair_history"])

    outputs_path = write_run_outputs(str(tmp_path), [output], [audit_record], [])
    evidence_rows = [
        json.loads(line)
        for line in Path(outputs_path["evidence"]).read_text(encoding="utf-8").splitlines()
    ]
    assert ONTOLOGY_PARTIAL_COMPOSITE_TISSUE_TYPE in evidence_rows[0]["evidence_by_field"][
        "tissue_type"
    ]["flags"]


def test_terminal_exact_full_string_with_and_is_not_split(monkeypatch) -> None:
    cfg = _load_stub_config()
    cfg.setdefault("rag", {}).setdefault("ontology", {})[
        "canonicalize_terminal_exact_labels"
    ] = True
    record = {
        "gsm_accession": "GSM5585965",
        "gse_accession": "GSE184398",
        "context_text": "Head and neck samples.",
    }
    outputs = [_make_output(gsm_accession="GSM5585965", tissue_type="head and neck")]
    fake_client = FakeLLMClient(outputs)
    monkeypatch.setattr(run_single_module, "create_llm_client", lambda _cfg: fake_client)

    calls: list[str] = []

    def _ground_tissue(raw_value: str, _context: str, _cfg: dict) -> OntologyMatch:
        calls.append(raw_value)
        if raw_value != "head and neck":
            raise AssertionError("Composite splitting should not occur for terminal exact full-string matches.")
        return _match_exact(
            raw_value,
            "head and neck region",
            "UBERON:0035810",
            match_type="synonym_exact",
            matched_via="synonym",
        )

    monkeypatch.setattr(
        ontology_validator,
        "_tissue_type_grounder",
        SimpleNamespace(ground_tissue_type=_ground_tissue),
    )

    output, audit_record, flagged = run_single_from_context_record(record, cfg)

    assert flagged is False
    assert output["tissue_type"] == "head and neck region"
    assert audit_record["attempts_by_field"].get("tissue_type", 0) == 0
    assert calls == ["head and neck"]


def test_composite_with_zero_fragment_exact_matches_preserves_existing_low_confidence() -> None:
    llm_output = {
        "gse_accession": "GSE184398",
        "gsm_accession": "GSM5585966",
        "data_type": "RNA-seq",
        "organism": "Homo sapiens",
        "tissue_type": "MysteryOne and MysteryTwo",
        "cell_line": "No",
        "disease": "Healthy",
        "treatment": "None",
    }

    def _ground_tissue(raw_value: str, _context: str, _cfg: dict) -> OntologyMatch:
        if raw_value == "MysteryOne and MysteryTwo":
            return _match_low_confidence(raw_value, "colon")
        return _match_no_match(raw_value)

    original_grounder = ontology_validator._tissue_type_grounder
    ontology_validator._tissue_type_grounder = SimpleNamespace(ground_tissue_type=_ground_tissue)
    try:
        matches, failures = ontology_validator.ground_all_fields(llm_output, "", {})
    finally:
        ontology_validator._tissue_type_grounder = original_grounder

    assert matches["tissue_type"].status == "LOW_CONFIDENCE"
    assert matches["tissue_type"].matched_via != "composite_partial_components"
    assert failures["tissue_type"] == ONTOLOGY_LOW_CONFIDENCE_TISSUE_TYPE


def test_composite_resolution_is_deterministic_across_runs(
    monkeypatch,
    tmp_path: Path,
) -> None:
    cfg = _load_stub_config()
    record = {
        "gsm_accession": "GSM5585967",
        "gse_accession": "GSE184398",
        "context_text": "Colon & Rectum tissues.",
    }

    def _ground_tissue(raw_value: str, _context: str, _cfg: dict) -> OntologyMatch:
        if raw_value == "Colon & Rectum":
            return _match_low_confidence(raw_value, "colon")
        if raw_value == "Colon":
            return _match_exact(raw_value, "colon", "UBERON:0001155")
        if raw_value == "Rectum":
            return _match_exact(raw_value, "rectum", "UBERON:0001052")
        return _match_no_match(raw_value)

    monkeypatch.setattr(
        ontology_validator,
        "_tissue_type_grounder",
        SimpleNamespace(ground_tissue_type=_ground_tissue),
    )

    fake_client_1 = FakeLLMClient(
        [_make_output(gsm_accession="GSM5585967", tissue_type="Colon & Rectum")]
    )
    monkeypatch.setattr(run_single_module, "create_llm_client", lambda _cfg: fake_client_1)
    output_1, audit_1, _ = run_single_from_context_record(record, cfg)

    fake_client_2 = FakeLLMClient(
        [_make_output(gsm_accession="GSM5585967", tissue_type="Colon & Rectum")]
    )
    monkeypatch.setattr(run_single_module, "create_llm_client", lambda _cfg: fake_client_2)
    output_2, audit_2, _ = run_single_from_context_record(record, cfg)

    assert output_1 == output_2
    assert audit_1["validation"] == audit_2["validation"]
    assert audit_1["rationale"] == audit_2["rationale"]
    assert audit_1["flags"] == audit_2["flags"]

    run1 = write_run_outputs(str(tmp_path / "run1"), [output_1], [audit_1], [])
    run2 = write_run_outputs(str(tmp_path / "run2"), [output_2], [audit_2], [])
    assert Path(run1["evidence"]).read_bytes() == Path(run2["evidence"]).read_bytes()
    assert Path(run1["curation_jsonl"]).read_bytes() == Path(run2["curation_jsonl"]).read_bytes()
