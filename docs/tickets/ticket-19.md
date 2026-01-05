# Ticket #19: AGENT-WS-019 — Evidence-first short-circuit in primary failure selection (ensure inferred-without-evidence repairs run before ontology low-confidence)

You are working in repo `geo-gsm-annotator-agent`.

## Context

Ticket #18 added decision-table routes and repair prompts for:

* `disease_inferred_without_evidence`
* `cell_line_inferred_without_evidence`

However, runs still prioritize ontology failures (for example `ontology_low_confidence_cell_line`) because the decision engine selects a single “primary failure” using `select_primary_failure_across_fields`, which ranks failures via `_failure_sort_key()`.

Result: evidence-based failures exist in `failures_by_field` but are not chosen, so the repair loop never uses the new evidence repair prompts.

We want a robust fix that does not depend on tuning severity/priority tables.

## Goal

Add an explicit **evidence-first short-circuit rule** in `select_primary_failure_across_fields` so that if any field contains an `*_inferred_without_evidence` failure, it is always selected as the primary failure before any ontology low-confidence failures.

This ensures Ticket #18 behavior triggers as intended.

## Non-goals

* Do not redesign the full failure ranking system.
* Do not change decision_table.yaml rules for Ticket #18 (they are already correct).
* Do not change ontology grounding logic.
* Do not change the 8-field output schema.

---

## Tasks

### A) Implement evidence-first short-circuit in failure selection

File:

* `src/validator/failure_codes.py`

Changes:

1. Define a small constant set near the selection functions (module-level is fine):

```python
EVIDENCE_FIRST_FAILURES = {
    "disease_inferred_without_evidence",
    "cell_line_inferred_without_evidence",
}
```

2. Update `select_primary_failure_across_fields(failures_by_field)`:

Before building candidates using `select_primary_failure(...)`, add a first pass:

* Scan every `field -> failures` list.
* If any failure code is in `EVIDENCE_FIRST_FAILURES`, select it immediately.

Determinism requirements:

* If multiple evidence-first failures exist across fields, choose deterministically.
* Use a stable ordering:

  * iterate fields in sorted order (`sorted(failures_by_field.keys())`)
  * within each field, scan failures in list order (or sorted order, but keep consistent)
* Return the first encountered evidence-first failure.

Example deterministic behavior:

* If both disease and cell_line have inferred-without-evidence, pick `cell_line` first (because `"cell_line"` sorts before `"disease"`), unless you choose a different explicit order.

3. If no evidence-first failures exist, fall back to the existing logic unchanged.

### B) Unit tests for evidence-first priority

Add file:

* `tests/test_failure_codes_evidence_first.py`

Test cases:

1. Evidence beats ontology low confidence:

```python
failures_by_field = {
  "cell_line": ["ontology_low_confidence_cell_line", "cell_line_inferred_without_evidence"],
}
```

Expected: selects `("cell_line", "cell_line_inferred_without_evidence")`.

2. Evidence in another field beats ontology failure in cell_line:

```python
failures_by_field = {
  "cell_line": ["ontology_low_confidence_cell_line"],
  "disease": ["disease_inferred_without_evidence"],
}
```

Expected: selects `("disease", "disease_inferred_without_evidence")`.

3. No evidence failures: behavior unchanged
   Use a simple map with only ontology failures and confirm it selects the same primary as before (choose an assertion that is stable in current codebase).

### C) Integration test (optional but recommended)

If you already have a stubbed end-to-end test framework, add one test verifying that when both:

* `cell_line_inferred_without_evidence`
* and `ontology_low_confidence_cell_line`
  are present, the repair loop uses `repair_cell_line_evidence_v1` first.

If this is hard to do cleanly, skip and rely on unit tests + existing Ticket #18 tests.

---

## Acceptance criteria

* `uv run pytest -q` passes.
* In a run where both evidence-inference failures and ontology low-confidence failures exist, the primary failure chosen is always an evidence-inference failure.
* Ticket #18 repairs (evidence prompts) are now reachable in normal runs.

---

## Ticket file requirement (MANDATORY)

After writing this ticket content, the AI coding agent must create:

* `docs/tickets/ticket-19.md`

and copy the full contents of this ticket verbatim into that file.
