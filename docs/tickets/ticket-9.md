Ticket #9: AGENT-WS-009 Implement single-GSM pipeline with stubs (+ unit tests)

This ticket produces the first end-to-end runnable “walking skeleton” for one GSM:
* stub parser produces context text
* stub LLM produces raw output (valid JSON)
* validators run
* decision/repair loop runs
* final output + audit record returned

You are working in repo `geo-gsm-annotator-agent` (src-layout under `src/`).

Ticket: AGENT-WS-009 — Implement single-GSM pipeline with stubs (+ unit tests)

Goal:
Implement `run_single_gsm()` in `src/agent/run_single.py` that orchestrates:
- stub parser -> context_text
- stub LLM -> raw output string
- format validator -> parsed dict + format errors
- semantic validator -> semantic errors
- consistency validator -> flags
- ontology grounding validator entrypoint -> matches + ontology_failures
- decision/repair loop -> final decision + final_output (with fallbacks as needed)
- audit record builder -> audit dict
Return (primary_output, audit_record, flagged_bool)

No real external calls in this ticket.

Files to implement/update:
- `src/agent/run_single.py` (currently placeholder)
- Add tests: `tests/test_run_single_stub.py`

Use existing modules:
- PipelineState: `agent.state.PipelineState`
- build_audit_record: `agent.audit.build_audit_record`
- validate_format: `validator.format_validator.validate_format`
- semantic_validate: `validator.semantic_validator.semantic_validate`
- consistency_validate: `validator.consistency_validator.consistency_validate`
- ground_all_fields: `validator.ontology_validator.ground_all_fields`
- apply_repairs: `agent.repair_loop.apply_repairs`
- load_decision_table: `validator.decision_engine.load_decision_table`

Implement stubs inside run_single.py only:
A) Stub parser:
- If cfg["parser"]["mode"] == "stub":
  - context_text = f"Series Accession: GSE000000\\nSample ID: {gsm_accession}\\nSample Organism: Homo sapiens\\nSample Molecular: total RNA\\nSample Library Strategy: RNA-Seq\\n"
  - parsed_jsonl can be None or same as context_text

B) Stub LLM:
- If cfg["llm"]["mode"] == "stub":
  - Return a raw JSON string that matches required keys.
  - Use gsm_accession and GSE000000.
  - Use values that will PASS validators by default:
    data_type: "RNA-seq"
    organism: "Homo sapiens"
    tissue_type: "Blood"
    cell_line: "No"
    disease: "Healthy"
    treatment: "None"

Main function signature:
- `run_single_gsm(gsm_accession: str, cfg: dict) -> tuple[dict, dict, bool]`

Implementation steps:
1) Create PipelineState with gsm_accession and versions from cfg["versions"].
2) Get context_text (stub parser).
3) Call stub LLM -> raw_output; append to state.llm_raw_outputs
4) Run validate_format(raw_output, expected_keys) -> parsed_output, format_errors
   - store in state.llm_parsed_outputs and state.format_errors
5) If parsed_output is None:
   - set final_decision="FLAGGED"
   - build audit and return empty primary_output dict (or fallback-only dict), flagged True
6) Run semantic_validate(parsed_output, context_text) -> store in state.semantic_errors
7) Run consistency_validate(parsed_output, context_text) -> store in state.consistency_flags
8) Run ground_all_fields(parsed_output, context_text, cfg["rag"]) -> matches, ontology_failures
   - store ontology matches as dict (use .to_dict())
   - store ontology_failures
9) Create failures_by_field for repair loop:
   - merge semantic_errors and ontology_failures
   - Also treat each consistency flag as a failure mapped to a field:
     - assay_platform_conflict -> data_type
     - single_cell_evidence_missing -> data_type
     - healthy_disease_conflict -> disease
     - organism_context_conflict -> organism (note: organism not ontology-validated here, but include for escalation)
10) Load decision_table from `spec/decision_table.yaml`
11) Initialize state.final_output as parsed_output copy
12) Call apply_repairs(state, decision_table, max_total_repairs=cfg["limits"].get("max_total_repairs"))
    - After return, set primary_output = state.final_output (must have 8 keys)
13) Build audit_record = build_audit_record(state)
14) flagged_bool = (state.final_decision != "ACCEPT")
15) Return (primary_output, audit_record, flagged_bool)

Important:
- Ensure primary_output always contains all 8 required keys:
  If any missing in parsed_output, fill with safe placeholders:
  - gse_accession/gsm_accession from known inputs
  - data_type: "Unknown"
  - organism: "Unknown"
  - tissue_type: "Unknown"
  - cell_line: "No"
  - disease: "Healthy"
  - treatment: "None"
Keep this minimal and deterministic.

Unit tests:
Create `tests/test_run_single_stub.py`:
- Load cfg from `config/example_config.yaml` using agent.config.load_config (or just build dict inline if config loader exists)
- Set llm.mode=stub, parser.mode=stub
- Call run_single_gsm("GSM000000", cfg)
- Assert:
  - primary_output has exactly 8 keys
  - flagged_bool is False (should ACCEPT)
  - audit_record has gsm_accession and validation keys
- Add a test where stub LLM returns invalid JSON (simulate by monkeypatching a helper inside run_single or by allowing cfg to set llm.stub_invalid_json=true):
  - flagged_bool True
  - audit_record.final_decision == "FLAGGED"

Constraints:
- No external network calls
- No Chroma dependency required (ontology validator is robust to placeholder grounders)
- Keep code readable and simple

After implementation:
- run `uv run python -m pytest -q`

Deliverables:
- `src/agent/run_single.py`
- `tests/test_run_single_stub.py`
