# Instructions for Proposing New Tickets

## Purpose

All tickets must align with the **currently implemented behavior** of the system.

- Code is authoritative.
- Policy documentation reflects current behavior.
- Tickets exist to change behavior in a controlled, auditable way.

No ticket may silently reinterpret system semantics.

---

## Mandatory Pre-check (Policy-Aware Development)

Before proposing **any** ticket:

1. **Read** the current policy document:
   - `docs/policies/policy-spec.md`

2. Determine whether the issue:
   - already follows existing policy
   - violates existing policy
   - requires a **policy change or extension**

If the ticket affects policy behavior, the policy document **must be updated**.

---

## UI vs Backend Scope Check (v1.0+, clarified in v1.1)

Before proposing a **UI-related** ticket, explicitly determine scope.

### UI-only tickets MAY do the following:
- Change presentation, layout, navigation, or ergonomics
- Improve transparency or inspection of backend artifacts
- Persist **explicit curator actions** (overrides, checked markers)
- Export derived artifacts (CSV, summaries) from existing backend outputs
- Support explicit, reversible bulk actions initiated by the curator

### UI tickets MUST NOT:
- Re-run backend validation, repair, or ontology grounding
- Reinterpret backend flags, failures, or confidence levels
- Synthesize new diagnostic signals
- Infer correctness from patterns across GSMs
- Propagate values across GSMs implicitly
- Introduce learning from curator edits
- Compensate silently for backend limitations

If **any** backend behavior would need to change, **stop** and propose a
backend-scoped ticket instead.

---

## Evidence and Diagnostics Rule (v1.1 invariant)

For UI tickets involving diagnostics or highlighting:

- `evidence.jsonl` is the **sole authoritative source** for per-field diagnostics
- UI must not invent, summarize, or reinterpret diagnostic signals
- Cell highlighting is permitted **if and only if**:
  `evidence_by_field[field].flags` is non-empty
- Fallback states are informational only unless explicitly flagged

Any UI ticket that violates this must be rejected.

---

## Bulk Actions and Safety Requirements (v1.1)

Tickets proposing bulk operations must explicitly state:

- what is being applied (single column, single value)
- the selection scope (explicit row selection only)
- preview behavior before apply
- reversibility guarantees
- validation or safety checks reused from single-edit semantics

Implicit, automatic, or inferred bulk operations are not allowed.

---

## Policy-Related Tickets (Required Rule)

If a ticket:
- introduces a new rule
- changes decision logic
- alters validation, repair, or fallback behavior
- changes ontology preference or interpretation
- changes the meaning of output fields

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

What real-world case, audit log, or curator experience triggered this issue.

## Problem Statement

What is incorrect, ambiguous, or inconsistent with current behavior.

## Proposed Change

What should change, stated precisely and operationally.

## Policy Impact

* [ ] No policy change
* [ ] Policy clarification only
* [ ] Policy change (policy-spec.md must be updated)

## Acceptance Criteria

Objective, testable conditions for completion.

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
