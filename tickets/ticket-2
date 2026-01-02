Ticket #2: AGENT-WS-002 Implement Decision engine

You are working in repo `geo-gsm-annotator-agent`.

Goal: implement the deterministic decision engine that maps validation failures to next actions, using the existing YAML decision table at `spec/decision_table.yaml`.

Scope:
- Implement:
  1) `src/validator/failure_codes.py`
  2) `src/validator/decision_engine.py`
- Do NOT implement full pipeline, LLM, parser, Chroma, or ontology validators.
- Keep this code self-contained and unit-testable.

Inputs and concepts:
- Validators will produce failures grouped by field:
  `failures_by_field: dict[str, list[str]]`
  Example:
    {
      "tissue_type": ["tissue_is_cell_type"],
      "data_type": ["ontology_no_match"]
    }
- We also track attempts:
  `attempts_by_field: dict[str, int]`  (how many repairs already tried for each field)

Decision table:
- YAML file `spec/decision_table.yaml` maps failure_code -> rule with:
  action: ACCEPT | REPAIR | FALLBACK | ESCALATE
  field: optional string or null (if null, use the failing field)
  repair_template: optional
  max_attempts: int
  fallback_value: optional
  severity: low/medium/high

Task A: Implement failure codes module
File: `src/validator/failure_codes.py`

Requirements:
- Define constants for all known failure codes (at least those in the YAML).
- Implement:
  - `PRIMARY_FAILURE_ORDER: list[str]` or a severity mapping.
  - `select_primary_failure(failures: list[str]) -> str`
    - Choose the highest-severity failure among the list.
    - If ties, use a stable priority order (define it).
- Implement:
  - `select_primary_failure_across_fields(failures_by_field: dict[str, list[str]]) -> tuple[str, str]`
    - Returns (field, failure_code) for the single failure to act on first.
    - Choose highest severity across all fields. If tie, deterministic (e.g., field name sort).
- Keep it deterministic.

Task B: Implement decision engine
File: `src/validator/decision_engine.py`

Requirements:
- Create a dataclass `Decision` with fields:
  - decision_type: str  (ACCEPT/REPAIR/FALLBACK/ESCALATE)
  - field: str | None
  - failure_code: str | None
  - repair_template: str | None
  - fallback_value: str | None
  - severity: str | None
- Implement:
  - `load_decision_table(path: str) -> dict`
  - `decide_next_action(failures_by_field: dict[str, list[str]], attempts_by_field: dict[str, int], decision_table: dict) -> Decision`
Rules:
1) If failures_by_field is empty -> ACCEPT.
2) Choose one (field, failure_code) to act on using `select_primary_failure_across_fields`.
3) Look up failure_code in decision_table; if missing -> ESCALATE with severity high.
4) Determine target field:
   - if decision_table[code].field is not null -> use it
   - else use the selected failing field
5) Enforce max_attempts:
   - current_attempts = attempts_by_field.get(target_field, 0)
   - if action is REPAIR and current_attempts >= max_attempts:
       - if fallback_value exists -> FALLBACK (use fallback_value)
       - else -> ESCALATE
6) If action is FALLBACK, always return FALLBACK with fallback_value.
7) If action is ESCALATE, return ESCALATE.
8) Ensure deterministic behavior.

No file I/O in decide_next_action except the separate load_decision_table helper.

Add minimal tests:
- Create `tests/test_decision_engine.py` with a few unit tests using a small inline decision_table dict (do not read YAML in tests).
Test cases:
- empty failures -> ACCEPT
- tissue_is_cell_type with attempts < max -> REPAIR tissue_type with repair_tissue_v1
- tissue_is_cell_type with attempts >= max -> FALLBACK tissue_type Unknown
- disease_unsupported -> FALLBACK Healthy
- unknown failure code -> ESCALATE

Notes:
- Keep imports minimal: standard library + pyyaml only if needed in load_decision_table.
- Do not change existing YAML file.

After implementation, run:
- `python -m pytest -q` (or equivalent) and ensure tests pass.

Deliverables:
- src/validator/failure_codes.py
- src/validator/decision_engine.py
- tests/test_decision_engine.py
