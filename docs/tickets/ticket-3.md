Ticket #3: AGENT-WS-003 Implement strict LLM output format validator (+ unit tests)

You are working in repo `geo-gsm-annotator-agent` (src-layout under `src/`).

Ticket: AGENT-WS-003 — Implement strict LLM output format validator (+ unit tests)

Goal:
Implement a strict format validator that takes raw LLM output text and enforces:
- valid JSON object
- exact required keys (8 keys)
- string values only
- non-empty values
- word-limit rule: <= 5 words per value
Return standardized error codes without raising.

IMPORTANT:
There is already a file `src/validator/format_validator.py` in the skeleton. You must REVIEW it and adjust it to fully meet the spec below. It might already be close; update as needed. Also add unit tests.

Spec:

Create/Update file: `src/validator/format_validator.py`

Public API:
- `validate_format(raw_output: str, expected_keys: list[str]) -> tuple[dict[str,str] | None, list[str]]`

Standardized error codes (exact strings):
- `invalid_json`
- `not_object`
- `missing_keys`
- `extra_keys`
- `non_string_value`
- `empty_value`
- `word_limit_violation`

Rules:
1) If JSON parsing fails -> return (None, ["invalid_json"])
2) If parsed JSON is not a dict -> return (None, ["not_object"])
3) Compare keys:
   - If any missing -> include "missing_keys"
   - If any extra -> include "extra_keys"
4) For each expected key that exists:
   - Must be a string else include "non_string_value"
   - After strip(), must be non-empty else include "empty_value"
   - Word count is number of whitespace-separated tokens; if > 5 include "word_limit_violation"
5) Return a parsed_output dict with stripped string values for keys that are present and valid strings (even if other errors exist). This is useful for partial repair.
6) De-duplicate error codes and return them sorted in a stable order (same order as listed above is preferred).
7) Do not do any semantic checks (no tissue/cell logic etc).

Add unit tests:
Create `tests/test_format_validator.py` with pytest tests.

Test cases (minimum):
- Invalid JSON -> invalid_json only
- JSON array -> not_object
- Missing key -> missing_keys
- Extra key -> extra_keys
- Non-string value -> non_string_value
- Empty string -> empty_value
- Word limit > 5 -> word_limit_violation
- Happy path -> no errors and correct parsed dict

Keep tests minimal and fast.

Constraints:
- Use only standard library + pytest.
- Do not modify other modules unless strictly necessary.
- Keep code simple and deterministic.

After implementation:
- run `uv run python -m pytest -q` and ensure all tests pass.

Deliverables:
- updated `src/validator/format_validator.py`
- new `tests/test_format_validator.py`
