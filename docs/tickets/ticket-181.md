# Ticket #181: Clarify `healthy_disease_conflict` as non-blocking informational flag

## Background

Case: GSE227108 / GSM7091755

- disease = "Healthy"
- treatment = "left intact, sham castration"
- consistency_flags includes: ["healthy_disease_conflict"]
- final_decision = ACCEPT

This behavior is correct.

Healthy samples may legitimately include interventions (e.g., sham surgery,
vehicle treatment, castration, dietary manipulation, etc.).
Therefore, coexistence of:
- disease = Healthy
- non-empty treatment

is biologically valid and must not cause FLAGGED decisions.

Currently:
- `healthy_disease_conflict` is emitted as a consistency flag
- It does not escalate decision
- However, this is not explicitly documented as a non-blocking flag in policy

We should codify this to prevent future semantic drift.

---

## Problem Statement

`healthy_disease_conflict` is currently treated as an informational consistency flag,
but policy documentation does not explicitly state that:

- It must not be considered a primary failure
- It must not escalate `final_decision` to FLAGGED

Without explicit documentation, future refactors could mistakenly treat it as blocking.

---

## Proposed Change

Update `docs/policies/policy-spec.md` to clarify:

### Disease = Healthy semantics

1. `"Healthy"` is a valid canonical non-disease value.
2. Presence of non-empty `treatment` alongside `"Healthy"`:
   - MUST NOT be treated as ontology failure.
   - MUST NOT escalate to FLAGGED.
   - MAY emit `healthy_disease_conflict` as informational consistency flag.

3. `healthy_disease_conflict`:
   - is informational only
   - must never be selected as `primary_failure`
   - must not affect `final_decision`

No code change required (behavior already correct).
This is a documentation-level invariant clarification.

---

## Policy Impact

[x] Policy change required (clarification only).

Update policy-spec.md:

- Add explicit section under consistency flags:
  - Define `healthy_disease_conflict`
  - Mark as non-blocking
  - Explicitly exclude from decision escalation

No change to whitepaper required.

---

## Acceptance Criteria

1. GSM7091755 remains ACCEPT.
2. `healthy_disease_conflict` may appear in `consistency_flags`.
3. `healthy_disease_conflict` is never selected as `primary_failure`.
4. Determinism preserved across reruns.
5. No regression in disease ontology behavior.

---

## Non-Goals

- No change to disease canonicalization logic.
- No change to treatment validation.
- No change to decision routing logic.
- No UI changes.

---

## Ticket file requirement (MANDATORY)

Create:

docs/tickets/ticket-181.md

Paste this ticket verbatim.
