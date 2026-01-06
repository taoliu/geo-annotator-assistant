# Ticket #25: AGENT-WS-025 — Field-specific word limits in format validation (disable for treatment)

### Background

In real GEO records, `treatment` often contains long, structured descriptions (reagents, antibodies, lots, constructs). The current format validator applies a fixed `>5 words` limit to **all** string fields, producing `word_limit_violation` even when output is structurally valid JSON.

This causes unnecessary format repair retries (`max_format_repairs`) and can lead to `format_unrepaired` and placeholder fallback outputs, as observed on GSM4909108 / GSE161517.

### Goal

Make the word limit check **field-specific**, with the default behavior preserved, but allow `treatment` to have no word limit (or a much higher one).

### Non-goals

* No prompt changes
* No decision table policy changes
* No architecture changes
* No change to semantic/ontology validation logic

### Required changes

#### 1) Update `validate_format()` signature (backward compatible)

File: `src/validator/format_validator.py`

Add an optional keyword-only argument:

* `word_limits: Optional[Dict[str, int]] = None`

Interpretation:

* If `word_limits` is not provided: keep current behavior (`>5` for all fields).
* If `word_limits[field]` is:

  * `0` or negative: disable word limit for that field
  * positive integer: use that as the per-field limit
  * not present: fall back to default (5)

Implementation detail:

* Only apply `_word_count` check when `limit > 0`.

#### 2) Wire config → validate_format in the pipeline

File: `src/agent/run_single.py`

In both places that call `validate_format()`:

* initial label output
* format repair attempts

Pass `word_limits` read from config, e.g.:

```python
word_limits = cfg.get("limits", {}).get("field_word_limits")
parsed_output, format_errors = validate_format(raw_output, REQUIRED_KEYS, word_limits=word_limits)
```

(Keep this change minimal and local.)

#### 3) Update example config(s)

File(s):

* `config/example_config.yaml` (and any config used for local_transformers if appropriate)

Add:

```yaml
limits:
  max_format_repairs: 2
  field_word_limits:
    treatment: 0
```

Do not remove existing keys.

#### 4) Add unit tests

File: `tests/test_format_validator.py` (or a new small test file if cleaner)

Add tests for:

1. Default behavior unchanged:

   * a field with >5 words triggers `word_limit_violation` when `word_limits` is not provided.
2. Field-specific override works:

   * `treatment` >5 words does **not** trigger `word_limit_violation` when `word_limits={"treatment": 0}`.
3. Optional: custom limit:

   * `word_limits={"treatment": 10}` triggers violation only if >10 words.

### Acceptance criteria

* Running a real-world record with long `treatment` no longer triggers `word_limit_violation` solely due to treatment length.
* Format repair loop is not entered purely because `treatment` is long.
* `uv run pytest -q` passes.

---

## Implementation notes (so Codex doesn’t overreach)

* Keep `ERROR_WORD_LIMIT` as-is (no new error code needed).
* Keep the default word limit = 5 for all fields except where overridden.
* Prefer minimal diff.

---

