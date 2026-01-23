# Ticket #73: Emit per-GSE JSONL summary of possible values per field (diagnostic only)

## Problem

The pipeline emits `gse_consistency.json` as an advisory diagnostic, but it is verbose for scanning many GSEs.
We want a compact, line-oriented summary artifact that lists, for each GSE and each field, the set of observed non-placeholder values.

## Scope (minimal, deterministic)

Add a new diagnostic output file (one line per GSE):

* `gse_field_values.jsonl`

For each GSE, emit:
* `gse_accession`
* `n_total`
* `ignore_values` (same as used in consistency)
* `fields`: mapping from field name to a list of observed non-placeholder values

Requirements:
* Deterministic ordering of values in each list (e.g., sort by descending count then lexicographic).
* This artifact is diagnostic-only and must not be used for GSM-level decision making.
* No changes to GSM outputs, decision routing, repair, grounding, or schema.

## Acceptance Criteria

1. The new file is created for a GSE run alongside existing outputs.
2. For each field, the value list contains all observed non-placeholder values.
3. Ordering is deterministic to support stable diffs.
4. Existing `gse_consistency.json` behavior is unchanged.

## Required Tests

Add a unit test that:
1. Constructs a small synthetic set of GSM outputs for one GSE with known field value variation.
2. Runs the consistency summarizer.
3. Asserts the emitted JSONL contains the expected value sets and deterministic ordering.

Run:
`uv run pytest -q`

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-73.md` and paste this ticket verbatim.
