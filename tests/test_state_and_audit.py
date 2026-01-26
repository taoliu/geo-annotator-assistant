from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agent.audit import build_audit_record
from agent.state import PipelineState
from validator.ontology_match import OntologyMatch


def test_pipeline_state_defaults() -> None:
    state = PipelineState(gsm_accession="GSM123")
    assert state.gse_accession is None
    assert state.input_hash is None
    assert state.parsed_jsonl is None
    assert state.context_text is None
    assert state.llm_raw_outputs == []
    assert state.llm_parsed_outputs == []
    assert state.llm_cache_hits == []
    assert state.llm_cache_enabled is False
    assert state.validation_cache_hit is False
    assert state.format_errors == []
    assert state.semantic_errors == {}
    assert state.consistency_flags == []
    assert state.ontology_matches == {}
    assert state.ontology_failures == {}
    assert state.attempts_by_field == {}
    assert state.repair_history == []
    assert state.terminal_fallback_fields == set()
    assert state.final_output is None
    assert state.final_decision is None
    assert state.flags == []
    assert state.versions == {}


def test_pipeline_state_to_dict_serializes_ontology_match() -> None:
    match = OntologyMatch(
        field="tissue_type",
        raw_value="Small intestine",
        ontology="UBERON",
        status="MATCHED",
        matched_term_id="UBERON:0002106",
        matched_label="small intestine",
        matched_source="Uberon Ontology",
        match_type="label_exact",
        score=0.9,
        alternates=[],
    )
    state = PipelineState(gsm_accession="GSM456", ontology_matches={"tissue_type": match})
    data = state.to_dict()
    serialized = data["ontology_matches"]["tissue_type"]
    assert isinstance(serialized, dict)
    assert serialized["ontology"] == "UBERON"
    assert serialized["status"] == "MATCHED"
    assert "matched_via" in serialized
    assert "matched_synonym" in serialized


def test_audit_record_json_and_timestamp() -> None:
    state = PipelineState(
        gsm_accession="GSM999",
        ontology_matches={"tissue_type": {"ontology": "EFO"}},
    )
    record = build_audit_record(state)
    assert record["validation"]["ontology_matches"]["tissue_type"]["ontology"] == "EFO"

    timestamp = record["timestamp"]
    assert "T" in timestamp
    assert timestamp.endswith("Z") or timestamp[-6] in {"+", "-"}

    dumped = json.dumps(record)
    assert isinstance(dumped, str)
