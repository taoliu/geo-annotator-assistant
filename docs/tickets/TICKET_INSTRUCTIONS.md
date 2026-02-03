# Instructions for Proposing New Tickets

## Purpose
All tickets must align with the **current implemented policies** of the system.
Code is authoritative, and policy documentation reflects current behavior.

## Mandatory Pre-check (Policy-Aware Development)
Before proposing **any** ticket:

1. **Read** the current policy document: `docs/policies/policy-spec.md`

2. Determine whether the issue:
- already follows existing policy
- violates existing policy
- requires a **policy change or extension**

If the ticket affects policy behavior, the policy document **must be updated**.

---

## UI vs Backend Scope Check (v1.0+)

Before proposing a **UI-related** ticket, explicitly determine:

- Does the change **only affect presentation, navigation, persistence of explicit overrides, or export of derived artifacts**?
  - If yes, it may be a UI ticket.
- Does the change alter:
  - validation or repair behavior
  - ontology matching or confidence thresholds
  - decision routing or flags
  - interpretation of backend outputs
  - schema or meaning of output fields
  - backend execution order

If **any** of the above are true, **stop** and propose a **backend-scoped ticket** instead.

UI tickets **must not** silently compensate for backend limitations.

---

## Policy-Related Tickets (Required Rule)
If a ticket:
- introduces a new rule
- changes decision logic
- alters validation, repair, or fallback behavior
- changes ontology preference or interpretation

Then the ticket **must include**:
- a section titled **“Policy Impact”**
- an explicit instruction to **update `policy-spec.md`**

No policy change is complete until documentation is updated.

---

## Standard Ticket Format (Required)

All tickets must use the following structure:

```markdown
# Ticket #XX: <Short descriptive title>

## Background

What real-world case or audit log triggered this issue.

## Problem Statement

What is incorrect, ambiguous, or inconsistent with current behavior.

## Proposed Change

What should change (behaviorally), stated precisely.

## Policy Impact

* [ ] No policy change
* [ ] Policy clarification only
* [ ] Policy change (policy-spec.md must be updated)

## Acceptance Criteria

Objective conditions to consider the ticket complete.

## Non-Goals

What this ticket explicitly does NOT address.

## Constraints
- Do not invent future behavior without evidence.
- Prefer deterministic rules over additional LLM calls.
- Prefer flagging over silent correction when ambiguity is high.
- Human curation must remain explicit and auditable.

## Guiding Principle
**Policies are written consequences of code, not aspirations.**  
If behavior changes, policy documentation must change with it.

## Ticket file requirement (MANDATORY)
Create `docs/tickets/ticket-XX.md` and paste this ticket verbatim.
