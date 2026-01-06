# Ticket #25: AGENT-WS-025 — Fix Transformers 4.57.3 generation warnings (attention_mask and sampling args)

## Background

When running the CLI with `llm.mode=local_transformers` under **Transformers 4.57.3**, the following warnings appear:

```
The following generation flags are not valid and may be ignored: ['temperature'].
The attention mask is not set and cannot be inferred from input because pad token is same as eos token.
```

Investigation shows this is caused by issues in `src/llm/local_transformers.py`:

1. `model.generate()` is called **without `attention_mask`**, while `pad_token_id == eos_token_id`, which Transformers explicitly warns can cause unreliable behavior.
2. Sampling-related parameters (`temperature`, `top_p`) are inconsistently handled relative to `do_sample`, triggering warnings about ignored flags.

This is a **Transformers API usage bug**, not a semantic or policy issue.

---

## Goal

Ensure that local Transformers generation is **API-correct and warning-free** under Transformers 4.57.3 by:

* Always passing a valid `attention_mask` to `model.generate()`
* Ensuring sampling parameters are only passed when `do_sample=True`
* Preserving existing decoding behavior and defaults

---

## Scope

### In scope

* Modify `src/llm/local_transformers.py`
* Adjust tokenization and generation calls to align with Transformers 4.57.3 expectations
* Add a minimal regression test to prevent future regressions

### Out of scope

* Changing prompts, repair logic, validation, or ontology behavior
* Changing default decoding policy (deterministic vs sampling)
* Introducing new configuration fields
* Refactoring LLM abstraction layers

---

## Required changes

### 1. Return `attention_mask` from tokenization

Update the prompt tokenization logic so that both `input_ids` and `attention_mask` are produced.

Key requirement:

* When using chat templates, render to text first, then tokenize, to guarantee `attention_mask` is available.

### 2. Pass `attention_mask` into `model.generate()`

Ensure `model.generate()` is always called with:

* `input_ids`
* `attention_mask`
* Explicit `pad_token_id` and `eos_token_id`

This removes the ambiguity warning when `pad_token_id == eos_token_id`.

### 3. Make sampling arguments internally consistent

Enforce the following invariant in generation calls:

* If `do_sample=False`:

  * Do **not** pass `temperature`, `top_p`, or other sampling-only parameters
* If `do_sample=True`:

  * Pass `temperature` and `top_p` as configured

This prevents Transformers from warning that generation flags are ignored.

---

## Acceptance criteria

### Functional

* Running the CLI no longer emits:

  * “generation flags … may be ignored: ['temperature']”
  * “attention mask is not set and cannot be inferred…”
* Generated text content remains functionally unchanged for deterministic decoding
* No change to output schema or downstream pipeline behavior

### Tests

Add at least one unit test that:

* Mocks `model.generate()`
* Asserts `attention_mask` is always passed
* Asserts:

  * `temperature` is **not** passed when `do_sample=False`
  * `temperature` **is** passed when `do_sample=True`

All tests must pass under:

```bash
uv run pytest -q
```

---

## Notes

* This ticket addresses a **library API compatibility issue**, not a modeling or policy decision.
* Fixing this early avoids silent decoding differences across Transformers versions.
* No milestone or whitepaper changes are required.

---

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-25.md` and paste this ticket verbatim.
