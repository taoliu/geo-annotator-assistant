# Ticket #82: Do not route healthy_disease_conflict (a consistency_flag) into repair loop failures; keep it as audit-only unless explicitly promoted

## Problem

`healthy_disease_conflict` is currently emitted by `consistency_validator.py` as a `consistency_flag`, then merged into repair-triggering failures via `_build_failures_by_field()` in:

* `run_single.py` (pre-repair loop)
* `repair_loop.py` (inside repair loop)

As a result, GSMs can enter repeated repair loops and end with `disease="Unknown"` even when:

* `validation.semantic_errors` is empty, and
* the LLM output `disease="Healthy"` is reasonable (e.g., vehicle control, no disease evidence)

This causes:
* unnecessary LLM calls
* loss of valid "Healthy" value
* confusing audit output where repairs occur without semantic_errors

## Scope (minimal, deterministic)

1. Treat `healthy_disease_conflict` as a non-repairing signal by default:
   * Keep emitting it (if desired) in `validation.consistency_flags` for reporting/diagnostics.
   * Do NOT include it in the failures fed into the repair decision engine.

2. Implement this by adding a small allow/deny gate in `_build_failures_by_field()` (both locations) so that:
   * `semantic_errors` remain repair-triggering
   * `ontology_failures` remain repair-triggering (as currently designed)
   * `consistency_flags` are included for reporting but only a safe subset (if any) can trigger repairs
   * specifically exclude `healthy_disease_conflict` from repair-triggering failures

No changes to:
* schema
* ontology grounding behavior
* decision table format
* UI artifacts

## Expected Behavior

For cases like GSE198867 / GSM5958328 (LLM outputs Healthy; no disease evidence):

* `validation.semantic_errors` stays empty
* `validation.consistency_flags` may include `healthy_disease_conflict` (optional, but allowed)
* repair loop does not run for disease due to this flag
* `n_llm_calls == 1`
* `final_output.disease` remains "Healthy"
* `terminal_fallback_fields` does not include "disease"

## Acceptance Criteria

1. `healthy_disease_conflict` no longer triggers repairs or additional LLM calls.
2. Other repair-triggering failures (semantic_errors / ontology_failures) behave unchanged.
3. Audit remains consistent: repairs only occur for failures that are actually routed into the decision engine.

## Required Tests

Add regression tests:

1. Healthy + vehicle control + no disease evidence:
   * no repair loop invocations for disease
   * `n_llm_calls == 1`
   * disease remains "Healthy"
   * optionally verify `healthy_disease_conflict` stays in `consistency_flags` (if still emitted)

2. A case with a real semantic error that should still trigger repair:
   * semantic_errors contains the failure
   * repair occurs as before

Run:
`uv run pytest -q`

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-82.md` and paste this ticket verbatim.
