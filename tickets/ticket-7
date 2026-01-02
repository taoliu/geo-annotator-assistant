Ticket #7: AGENT-WS-007 Implement PipelineState + audit record builder (+ unit tests)

You are working in repo `geo-gsm-annotator-agent` (src-layout under `src/`).

Ticket: AGENT-WS-007 — Implement PipelineState + audit record builder (+ unit tests)

Goal:
Implement:
1) `PipelineState` dataclass to hold per-GSM pipeline state
2) An audit record builder that converts state + validation results into a JSON-serializable dict

Do NOT implement the full pipeline orchestration yet. This ticket is about data structures.

Files to implement/update:
- `src/agent/state.py` (currently placeholder)
- `src/agent/audit.py` (currently placeholder)
- Add tests: `tests/test_state_and_audit.py`

Requirements:

A) PipelineState (agent/state.py)
Create a dataclass `PipelineState` with at least these fields:
- gsm_accession: str
- gse_accession: str | None = None
- input_hash: str | None = None
- parsed_jsonl: str | None = None
- context_text: str | None = None

- llm_raw_outputs: list[str]    # first proposal + repair outputs as raw strings
- llm_parsed_outputs: list[dict]  # parsed dicts after format validator (optional elements allowed)

- format_errors: list[str]
- semantic_errors: dict[str, list[str]]
- consistency_flags: list[str]
- ontology_matches: dict[str, Any]   # field -> OntologyMatch.to_dict()
- ontology_failures: dict[str, str]  # field -> failure_code

- attempts_by_field: dict[str, int]
- repair_history: list[dict]  # each entry contains failure_code, field, template, timestamp(optional)

- final_output: dict[str, str] | None
- final_decision: str | None  # ACCEPT / FLAGGED / FAILED
- flags: list[str]

- versions: dict[str, str]  # prompt_version, validator_version, rag_version

Methods:
- `to_dict()` returning JSON-serializable dict (convert OntologyMatch objects via to_dict if present)
- Provide safe defaults (empty lists/dicts)

B) Audit record builder (agent/audit.py)
Implement:
- `build_audit_record(state: PipelineState) -> dict`

Audit record keys (must exist, can be None):
- gsm_accession
- gse_accession
- input_hash
- versions
- llm_raw_outputs
- llm_parsed_outputs
- validation:
    - format_errors
    - semantic_errors
    - consistency_flags
    - ontology_matches
    - ontology_failures
- repair_history
- attempts_by_field
- final_output
- final_decision
- flags
- timestamp (UTC ISO8601 string)

Constraints:
- No file I/O
- No external deps
- Deterministic ordering where possible (e.g., sort dict keys in tests if needed)

Unit tests (pytest):
Create `tests/test_state_and_audit.py`:
- Instantiate PipelineState with minimal fields and ensure defaults are correct
- Add a fake ontology match dict and ensure audit record includes it
- Ensure timestamp exists and is ISO-like (can just check it contains "T" and ends with "Z" or has offset)
- Ensure build_audit_record output is JSON-serializable (json.dumps works)

After implementation:
- run `uv run python -m pytest -q`

Deliverables:
- `src/agent/state.py`
- `src/agent/audit.py`
- `tests/test_state_and_audit.py`
