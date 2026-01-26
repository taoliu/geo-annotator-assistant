from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agent.config import load_config
from agent.run_single import run_single_from_context_record
from llm.base import LLMRequest, LLMResult, compute_request_fingerprint


def _load_stub_config() -> dict:
    cfg = load_config(str(ROOT / "config" / "example_config.yaml"))
    cfg.setdefault("llm", {})["transport"] = "stub"
    cfg.setdefault("rag", {}).setdefault("ontology", {})["enabled"] = False
    return cfg


class _HealthyMouseClient:
    def generate(self, request: LLMRequest) -> LLMResult:
        output = {
            "gse_accession": "GSE000000",
            "gsm_accession": "GSM000000",
            "data_type": "RNA-seq",
            "organism": "Mus musculus",
            "tissue_type": "Liver",
            "cell_line": "No",
            "disease": "Healthy",
            "treatment": "None",
        }
        return LLMResult(
            text=json.dumps(output, ensure_ascii=True),
            request_id=request.request_id,
            usage=None,
            transport_meta={"provider": "test"},
            request_fingerprint=compute_request_fingerprint(request),
        )


def test_healthy_vehicle_control_no_conflict() -> None:
    cfg = _load_stub_config()
    record = {
        "context_text": (
            "Series Accession: GSE123\n"
            "Sample ID: GSM001\n"
            "Sample Organism: Mus musculus\n"
            "Sample Title: control sample\n"
            "Sample Characteristics: treatment=vehicle control\n"
        ),
        "gsm_accession": "GSM001",
        "gse_accession": "GSE123",
    }

    annotation, audit, flagged = run_single_from_context_record(
        record,
        cfg,
        llm_client=_HealthyMouseClient(),
    )

    assert annotation["disease"] == "Healthy"
    assert audit["final_decision"] == "ACCEPT"
    assert audit["rationale"]["n_llm_calls"] == 1
    assert "disease" not in audit["rationale"]["terminal_fallback_fields"]
    assert not any(entry.get("field") == "disease" for entry in audit["repair_history"])
    assert flagged is False


def test_healthy_with_disease_cue_does_not_trigger_repair() -> None:
    cfg = _load_stub_config()
    record = {
        "context_text": (
            "Series Accession: GSE123\n"
            "Sample ID: GSM002\n"
            "Sample Organism: Mus musculus\n"
            "Sample Title: tumor model control\n"
            "Sample Characteristics: treatment=vehicle control\n"
        ),
        "gsm_accession": "GSM002",
        "gse_accession": "GSE123",
    }

    annotation, audit, flagged = run_single_from_context_record(
        record,
        cfg,
        llm_client=_HealthyMouseClient(),
    )

    assert annotation["disease"] == "Healthy"
    assert audit["rationale"]["n_llm_calls"] == 1
    assert audit["validation"]["consistency_flags"] == ["healthy_disease_conflict"]
    assert not any(entry.get("field") == "disease" for entry in audit["repair_history"])
    assert flagged is False


def test_semantic_error_still_triggers_repair() -> None:
    cfg = _load_stub_config()

    class _CancerClient:
        def generate(self, request: LLMRequest) -> LLMResult:
            output = {
                "gse_accession": "GSE000000",
                "gsm_accession": "GSM000000",
                "data_type": "RNA-seq",
                "organism": "Mus musculus",
                "tissue_type": "Liver",
                "cell_line": "No",
                "disease": "Cancer",
                "treatment": "None",
            }
            return LLMResult(
                text=json.dumps(output, ensure_ascii=True),
                request_id=request.request_id,
                usage=None,
                transport_meta={"provider": "test"},
                request_fingerprint=compute_request_fingerprint(request),
            )

    record = {
        "context_text": (
            "Series Accession: GSE123\n"
            "Sample ID: GSM003\n"
            "Sample Organism: Mus musculus\n"
            "Sample Title: control sample\n"
            "Sample Characteristics: treatment=vehicle control\n"
        ),
        "gsm_accession": "GSM003",
        "gse_accession": "GSE123",
    }

    _, audit, flagged = run_single_from_context_record(
        record,
        cfg,
        llm_client=_CancerClient(),
    )

    assert audit["rationale"]["n_llm_calls"] > 1
    assert any(
        entry.get("failure_code") == "disease_inferred_without_evidence"
        for entry in audit["repair_history"]
    )
    assert flagged is True
