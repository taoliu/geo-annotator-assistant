# Ticket #81: Treat "Healthy" as a terminal disease value; suppress healthy_disease_conflict when no disease evidence exists

## Problem

In some GSMs, the LLM correctly outputs:

    disease = "Healthy"

However, the validator triggers `healthy_disease_conflict`, repeatedly invokes the repair loop, and ultimately forces:

    disease = "Unknown"

This happens even when:
* no disease terms appear in context
* no ontology-backed disease match exists
* treatment-only information is present (e.g. "Vehicle control")

This behavior is incorrect and causes:
* loss of valid information ("Healthy" → "Unknown")
* unnecessary LLM calls
* misleading audit trails

## Example

GSE198867 / GSM5958328:

* LLM outputs "Healthy" consistently
* No disease evidence in context
* Repair loop fires 3 times
* Final disease forced to "Unknown"

This violates current semantics where "Healthy" is a legitimate terminal value.

## Root Cause

The `healthy_disease_conflict` rule is too aggressive and treats "Healthy" as a hypothesis requiring corroboration, rather than a terminal value.

Treatment presence or experimental setup alone should not invalidate "Healthy".

## Scope (Minimal, No Redesign)

Update disease validation logic as follows:

* If `disease == "Healthy"`:
  * Do NOT trigger `healthy_disease_conflict` **unless**
    * an explicit disease term is present in context, OR
    * an ontology-backed disease match exists elsewhere
* Do NOT infer disease from treatment-only context
* Skip disease repair loop entirely when above conditions are met

No changes to:
* schema
* ontology databases
* decision routing
* UI artifacts

## Expected Behavior

For GSMs like the example:

* `disease = "Healthy"` is preserved
* `n_llm_calls = 1`
* `terminal_fallback_fields` does NOT include disease
* `final_decision = ACCEPT`
* No repair history entries for disease

## Required Tests

Add regression tests covering:

1. Mouse tissue + vehicle control + no disease terms → disease remains "Healthy"
2. Disease term explicitly present in context → healthy_disease_conflict still triggers
3. Ontology-backed disease match present → healthy_disease_conflict still triggers

Run:
    uv run pytest -q

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-81.md` and paste this ticket verbatim.
