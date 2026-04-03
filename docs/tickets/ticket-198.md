# Ticket #198: Bound no-op repair iterations for terminal fallback and locked fields

## Background

Long-running `geo-gsm-annotate` GSE jobs must preserve the architectural invariant of
bounded repair loops. During investigation of `testing_data/GSE297202_family.soft.gz`,
an HPC run reported `GSM8986011` repeating:

- validation completed
- ontology grounding started
- ontology grounding completed

without additional LLM calls and without hitting `limits.max_total_repairs`.

## Problem Statement

`src/agent/repair_loop.py` contains no-op branches where the selected field is already
authoritative:

- the field is already locked
- the field is already marked as terminal fallback
- a FALLBACK decision selects the same value already present in `final_output`

These branches currently clear the routed failure, invoke the validation callback
again, and continue without incrementing attempts. If validation deterministically
reintroduces the same routed failure for the unchanged field, the loop can spin
forever because `max_total_repairs` is keyed to `attempts_by_field`.

## Proposed Change

Update `apply_repairs()` so that no-op authoritative branches do **not** trigger
another validation pass when `final_output` has not changed.

### Required behavior

1. When decision routing selects a field that is already locked, clear the routed
   failure and continue without invoking `validation_callback`.
2. When decision routing selects a field already recorded in
   `terminal_fallback_fields`, clear the routed failure and continue without invoking
   `validation_callback`.
3. When a FALLBACK decision selects the same value already present in
   `state.final_output[field]`, record terminal fallback status when applicable, clear
   the routed failure, and continue without invoking `validation_callback`.
4. Preserve existing revalidation behavior after **real output changes**:
   - successful REPAIR merges
   - first-time FALLBACK value updates
5. Preserve existing audit fields, schema, and deterministic decision routing.

## Layer Affected

- [ ] Canonicalization
- [ ] Ontology grounding
- [x] Validation / Repair
- [ ] Decision routing
- [ ] UI only
- [ ] Documentation only

## Policy Impact

- [ ] No policy change
- [ ] Policy clarification only
- [x] Policy change (policy-spec.md must be updated)

This ticket changes repair-loop execution semantics for no-op authoritative branches.
The policy spec must document that unchanged authoritative values are cleared without a
fresh validation pass to preserve bounded convergence.

## Acceptance Criteria

1. A routed failure targeting an already locked field does not cause repeated
   validation/ontology passes when the output value is unchanged.
2. A routed failure targeting a terminal fallback field does not cause repeated
   validation/ontology passes when the output value is unchanged.
3. A FALLBACK decision that resolves to the field's current value does not invoke
   `validation_callback`.
4. Existing behavior is preserved when a repair or fallback actually changes
   `final_output`.
5. Add regression tests covering:
   - direct no-op fallback branch behavior
   - `GSM8986011` context from `testing_data/GSE297202_family.soft.gz` with repeated
     `data_type` consistency failure reintroduction
6. `uv run pytest -q` passes.

## Non-Goals

- Redesigning the decision engine.
- Changing output schema or audit structure.
- Changing ontology matching thresholds or repair prompts.
- Introducing cross-run persistence for loop counters.

## Constraints

- Keep the patch minimal and local to repair-loop orchestration.
- Do not weaken field locks or terminal fallback semantics.
- Do not add hidden retry counters outside current state/audit structures.

## Guiding Principle

If a repair-loop branch leaves `final_output` unchanged and the selected field is
already authoritative, the controller must not re-run validation for that same
unchanged state.
