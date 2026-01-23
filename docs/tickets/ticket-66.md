# Ticket #66: Clear audit primary_failure after successful repair when final validation is clean

## Problem

In some ACCEPT cases, the audit `rationale.primary_failure` reports a failure that was repaired away.

Example pattern:
* `repair_history` includes a repair for a failure code (e.g., `disease_inferred_without_evidence`) with `output_updated: true`
* final `validation.semantic_errors` is empty
* `final_decision` is `ACCEPT`
But `rationale.primary_failure` still reports the earlier failure code.

This produces misleading diagnostics and causes UI/review to treat clean ACCEPT records as having unresolved failures.

## Scope (minimal)

Update audit rationale construction so that `rationale.primary_failure` reflects the **final post-repair validation state** only.

Rules:
* If final validation contains no remaining failures, `rationale.primary_failure` must be empty/None/omitted (consistent with existing audit schema).
* If failures remain, `rationale.primary_failure` must match the deterministically selected primary failure from the final validation state.

No changes to:
* decision routing logic
* validation rules
* repair templates
* ontology grounding semantics
* output schema

## Acceptance Criteria

1. For a repaired-and-clean ACCEPT case, `rationale.primary_failure` is not populated with a repaired-away failure.
2. FLAGGED cases remain unchanged and still report their final primary failure.
3. No change to final output values or decisions.

## Required Tests

Add a regression test that simulates:
1. A GSM where an initial disease unsupported-inference failure triggers one repair that neutralizes the value and removes the error.
2. Final validation is clean and decision is ACCEPT.
3. Assert `rationale.primary_failure` is empty/None/omitted and `flags` is empty.

Run:
`uv run pytest -q`

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-66.md` and paste this ticket verbatim.
