Ticket #16-b: AGENT-WS-016b  

You are working in repo `geo-gsm-annotator-agent`.

Ticket: AGENT-WS-016b — Fix format-repair loop control flow + add JSON extraction for fenced/noisy outputs

Observed bug:
With local transformers, audit shows multiple LLM attempts:
- Attempt #1 is valid JSON but violates word limit
- Attempts #2/#3 return fenced JSON (```json ... ```) plus extra commentary
Pipeline ends with:
- format_errors: ["invalid_json"]
- flags: ["format_unrepaired"]
- final_decision: FLAGGED
even though at least one attempt contains a parseable JSON object.

This indicates:
1) The format-repair loop does not stop at first successful format validation.
2) The format validator fails to extract JSON from fenced/noisy model output.
3) Final format_errors is being overwritten by last attempt even if an earlier attempt passed.

Goal:
A) Make format repair loop stop at the FIRST attempt that yields a dict that passes format validation.
B) Make format validator robust: if raw output is not pure JSON, extract the first JSON object (including fenced blocks) and parse it.
C) Add regression tests reproducing the exact failure pattern.

Files to update:
- `src/validator/format_validator.py`
- `src/agent/run_single.py`
- Add tests: `tests/test_format_repair_extraction.py`

A) Update format validator: JSON extraction
In `validator/format_validator.py` (or helper file inside validator), implement:

1) `extract_json_candidate(text: str) -> str | None`
Must handle:
- Markdown fenced blocks:
  - If text contains ```json ... ``` return content inside first such fenced block
  - else if contains ``` ... ``` return content inside first fenced block
- Otherwise, find first '{' and extract a balanced JSON object:
  - scan characters, track brace depth
  - handle strings and escapes (ignore braces inside quoted strings)
  - return substring from first '{' to matching closing '}' when depth returns to 0
If no candidate found, return None.

2) Modify validate_format(raw_text, expected_keys, ...) to:
- First try json.loads(raw_text)
- If fails:
  - candidate = extract_json_candidate(raw_text)
  - if candidate: try json.loads(candidate)
- If still fails: return (None, ["invalid_json"] + other info as currently)
IMPORTANT: Do not change other existing format rules besides improving parsing robustness.

Ensure that when parsing succeeds, the validator uses the parsed dict for downstream checks (keys, word limits, etc).

B) Fix format repair loop in `agent/run_single.py`
Locate the "format repair pre-loop" logic. Ensure:

- It iterates attempts: initial + up to max_format_repairs
- For each attempt:
  - raw = llm.generate(...)
  - append raw to state.llm_raw_outputs
  - parsed, errors = validate_format(raw, expected_keys)
  - if parsed is not None: append parsed to state.llm_parsed_outputs (append-only)
  - if errors is empty:
      - accept this parsed output as the proposal
      - set state.format_errors = []
      - break out of the loop immediately
  - else:
      - keep last errors in a local variable (do not overwrite state.format_errors yet)
      - continue to next attempt

After loop:
- If no attempt succeeded:
  - set state.format_errors = last_errors
  - set state.final_decision="FLAGGED"
  - add state.flags += ["format_unrepaired"]
  - build audit and return

Also ensure you do NOT set final_decision=FLAGGED merely because state.flags is non-empty (this was fixed in WS-014).
Only flag here if format is unrepaired.

C) Update repair_format_v1 prompt (optional but recommended)
If `prompts/repair_format_v1.txt` exists, strengthen with one line:
- "Return raw JSON only. Do not use code fences. Do not add commentary."
This reduces reliance on extraction, but extraction must still exist.

D) Add tests: `tests/test_format_repair_extraction.py`

Test 1: validator extracts fenced JSON
- raw = "Here is JSON:\n```json\n{...}\n```\nSome text"
- validate_format should parse and return parsed dict (format errors may exist depending on values).
- assert "invalid_json" is NOT present.

Test 2: validator extracts first balanced JSON
- raw = "prefix {\"a\":1} suffix"
- extraction works and parses (use expected_keys accordingly)

Test 3: run_single stops at successful repair attempt
- Use a FakeLLM client (queue of outputs):
  - attempt1: valid JSON but violates word_limit (treatment too long)
  - attempt2: fenced JSON with short values (passes)
  - attempt3: garbage (should NOT be used if loop stops correctly)
- Monkeypatch llm.factory.create_llm_client to return FakeLLM.
- Run run_single_from_context_record with max_format_repairs >= 2.
- Assert:
  - state/audit indicates ACCEPT (or at least not format_unrepaired)
  - llm_raw_outputs length == 2 (stop early)
  - format_errors == []

If run_single_from_context_record returns only (primary, audit, flagged), assert flagged False.

E) Run full test suite:
- `uv run python -m pytest -q`

Acceptance criteria:
- Existing tests still pass.
- New tests pass.
- Re-running your local transformers JSONL job should no longer fail with invalid_json due to fences.
- Format repairs should stop at first successful attempt rather than being overwritten by later failures.

Deliverables:
- updated validator/format_validator.py with extraction
- updated agent/run_single.py loop logic
- new tests/test_format_repair_extraction.py
- (optional) updated prompts/repair_format_v1.txt
