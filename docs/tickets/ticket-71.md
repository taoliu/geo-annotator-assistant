# Ticket #71: Deterministic salvage for truncated/invalid JSON when corruption is confined to the last field (treatment)

## Problem

Some LLM raw outputs are nearly valid JSON but end truncated due to runaway repetition in the final field (often `treatment`), causing `format_errors: ["invalid_json"]`.
Example: output contains correct values for the first fields, but the `treatment` string is extremely long and the JSON is missing a valid closure (`"` / `}`).

We want to rescue these outputs deterministically when it is safe to do so, instead of discarding the whole proposal.

## Scope (minimal, deterministic)

Add a format-repair step that runs only when:

1. JSON parsing fails with `invalid_json`, AND
2. the raw output contains a recognizable JSON object prefix with required keys, AND
3. the corruption occurs in the last field (specifically `treatment`), consistent with truncation/unclosed quote/brace.

Repair action:

* deterministically truncate the `treatment` value to a fixed max character length (configurable or constant in code, e.g. 256 or 512)
* close the JSON string and object to produce valid JSON
* re-run JSON parsing on the repaired string
* continue pipeline using the repaired parsed output

The repair must be:
* field-scoped (treatment only)
* attempt-bounded
* auditable (record repair type, original length, truncated length)

No changes to:
* output schema (still 8 fields)
* ontology grounding semantics
* decision routing rules

## Acceptance Criteria

1. Given a raw LLM output that is valid up to `treatment` but truncated mid-string and missing closure, the system deterministically produces a valid parsed output with:
   * all earlier fields preserved exactly
   * `treatment` truncated to the configured limit
2. The record no longer has `format_errors: ["invalid_json"]` after repair.
3. The audit artifact records that a format salvage was applied (repair type + lengths).
4. Determinism preserved.

## Required Tests

Add a regression test that:
1. Feeds a synthetic LLM raw output that:
   * includes all required keys
   * has an overlong `treatment` string
   * is truncated before closing quotes/braces
2. Asserts the repair produces valid JSON and parsed dict.
3. Asserts only `treatment` was modified (truncated) and earlier fields unchanged.

Run:
`uv run pytest -q`

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-71.md` and paste this ticket verbatim.
