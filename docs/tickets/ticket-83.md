# Ticket #83: Exclude non-repairing consistency flags from rationale.primary_failure

## Problem

After Ticket #82, `healthy_disease_conflict` is correctly treated as a non-repairing `consistency_flag`:

* `semantic_errors` is empty
* `repair_history` is empty
* `final_output` is correct
* `final_decision = ACCEPT`

However, `rationale.primary_failure` is still populated with:

    "primary_failure": "healthy_disease_conflict"

This is misleading because:
* no repair was triggered
* no decision routing was affected
* the GSM is accepted without fallback

`primary_failure` should represent the primary **repair-triggering or decision-affecting** failure, not an informational consistency flag.

## Scope (Minimal)

Update `primary_failure` selection logic so that:

* Only failures that actually participate in decision routing or repair triggering can populate `rationale.primary_failure`
* Non-repairing `consistency_flags` (including `healthy_disease_conflict`) must NOT be selected as `primary_failure`

This change affects reporting only.

No changes to:
* validation logic
* repair routing
* ontology grounding
* output schema
* UI behavior

## Expected Behavior

For cases like GSE198867 / GSM5958328:

* `validation.consistency_flags` may include `"healthy_disease_conflict"`
* `semantic_errors` is empty
* `repair_history` is empty
* `final_decision = ACCEPT`
* `rationale.primary_failure` is **null or empty**

For cases where a real semantic or ontology failure triggers repair or affects routing:

* `primary_failure` continues to be populated as before

## Acceptance Criteria

1. `primary_failure` is empty for ACCEPTed GSMs with:
   * no semantic errors
   * no repairs
2. `primary_failure` remains populated for GSMs where a real failure affects routing or repair.
3. Audit output is internally consistent and interpretable.

## Required Tests

Add regression tests covering:

1. Healthy + vehicle control example:
   * `primary_failure` is null/empty
   * consistency_flags may include `healthy_disease_conflict`
2. A GSM with a real semantic error:
   * `primary_failure` is populated correctly

Run:
    uv run pytest -q

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-83.md` and paste this ticket verbatim.
