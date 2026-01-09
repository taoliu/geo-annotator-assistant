# Ticket #48: LLM-TRANSPORT-004 — Apply configured stop tokens consistently in OpenAI HTTP transport

## Background

Local HF transport trims model outputs using configured `stop` tokens (e.g. removing `<|eot_id|>`). The OpenAI HTTP transport must apply the same trimming so downstream parsing/validation sees consistent text across transports.

---

## Scope (STRICT)

### In scope

1. Add a shared stop-trimming helper:

   * Create `src/llm/text_postprocess.py`
   * Implement:

   ```python
   def apply_stop(text: str, stop_list: list[str] | None) -> str:
       ...
   ```

   Behavior must match existing `LocalTransformersClient._apply_stop`.

2. Update `src/llm/openai_http.py`:

   * After extracting `text` from the HTTP response, call `apply_stop(text, request.stop)` (or equivalent field).
   * Ensure trimming happens before returning `LLMResult`.

3. (Optional, preferred) Update `src/llm/local_transformers.py`:

   * Replace the existing `_apply_stop` implementation with a call to the shared helper, preserving behavior.

### Out of scope

* Any prompt changes
* Any validator/decision/repair changes
* Any new stop token defaults (use existing config behavior only)
* Any llama.cpp-specific adapter

---

## Acceptance Criteria

1. With `stop: ["<|eot_id|>"]` configured, both transports remove everything from the first occurrence onward.
2. All existing tests pass.
3. New test(s) pass demonstrating consistent trimming behavior.

---

## Tests Required

Add `tests/test_llm_stop_trimming.py`:

1. Unit test for `apply_stop`:

   * No stop list → returns original text
   * Stop token present → trims at earliest match
   * Multiple stop tokens → trims at earliest match among them

2. Integration-level test (lightweight):

   * For local_transformers: call helper directly or via a small stubbed path.
   * For openai_http: mock response content containing `<|eot_id|>` and assert `LLMResult.text` is trimmed.

---

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-48.md` and paste this ticket verbatim.

---
