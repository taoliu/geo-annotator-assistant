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
import agent.run_single as run_single_module
import validator.ontology_validator as ontology_validator
from llm.base import LLMRequest, LLMResult, compute_request_fingerprint
from validator.ontology_match import OntologyMatch
from validator.ontology_validator import normalize_tissue_type_for_grounding


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
        "gse_accession": "GSE000111",
        "gsm_accession": "GSM000333",
        "data_type": "RNA-seq",
        "organism": "Homo sapiens",
        "tissue_type": "peripheral blood",
        "cell_line": "No",
        "disease": "Healthy",
        "treatment": "None",
    }
    base.update(overrides)
    return json.dumps(base, ensure_ascii=True)


def _match_exact(raw_value: str, label: str, term_id: str) -> OntologyMatch:
    return OntologyMatch(
        field="tissue_type",
        raw_value=raw_value,
        ontology="Uberon Ontology",
        status="MATCHED",
        matched_term_id=term_id,
        matched_label=label,
        matched_source="Uberon Ontology",
        match_type="label_norm_exact",
        score=1.0,
        alternates=[],
        matched_via="label_norm",
    )


def _match_low_confidence(raw_value: str) -> OntologyMatch:
    return OntologyMatch(
        field="tissue_type",
        raw_value=raw_value,
        ontology="Uberon Ontology",
        status="LOW_CONFIDENCE",
        matched_term_id=None,
        matched_label=None,
        matched_source=None,
        match_type="jaccard",
        score=0.5,
        alternates=[],
    )


def test_normalize_tissue_type_for_grounding_exact_peripheral_blood() -> None:
    assert normalize_tissue_type_for_grounding("peripheral blood") == "blood"
    assert normalize_tissue_type_for_grounding("  Peripheral   Blood  ") == "blood"


def test_normalize_tissue_type_for_grounding_does_not_rewrite_pbmc() -> None:
    assert (
        normalize_tissue_type_for_grounding("peripheral blood mononuclear cells")
        == "peripheral blood mononuclear cells"
    )
    assert normalize_tissue_type_for_grounding("PBMC") == "PBMC"


def test_pipeline_rewrites_peripheral_blood_before_grounding(monkeypatch) -> None:
    cfg = _load_stub_config()
    record = {
        "gsm_accession": "GSM000333",
        "gse_accession": "GSE000111",
        "context_text": "Peripheral blood samples were profiled.",
    }
    outputs = [_make_output(tissue_type="peripheral blood")]
    fake_client = FakeLLMClient(outputs)
    monkeypatch.setattr(run_single_module, "create_llm_client", lambda _cfg: fake_client)

    calls: list[str] = []

    def _ground_tissue(raw_value: str, _context: str, _cfg: dict) -> OntologyMatch:
        calls.append(raw_value)
        if raw_value == "blood":
            return _match_exact(raw_value, "blood", "UBERON:0000178")
        if raw_value == "peripheral blood":
            return _match_low_confidence(raw_value)
        return _match_low_confidence(raw_value)

    monkeypatch.setattr(
        ontology_validator,
        "_tissue_type_grounder",
        SimpleNamespace(ground_tissue_type=_ground_tissue),
    )

    output, audit_record, flagged = run_single_from_context_record(record, cfg)

    assert flagged is False
    assert output["tissue_type"] == "blood"
    assert audit_record["validation"]["ontology_matches"]["tissue_type"]["status"] == "MATCHED"
    assert (
        audit_record["validation"]["ontology_matches"]["tissue_type"]["matched_term_id"]
        == "UBERON:0000178"
    )
    assert "ontology_low_confidence_tissue_type" not in audit_record["flags"]
    assert audit_record["attempts_by_field"].get("tissue_type", 0) == 0
    assert calls == ["blood"]
