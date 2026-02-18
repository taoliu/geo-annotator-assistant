# Instructions for Proposing New Tickets

## Purpose

All tickets must align with the **currently implemented behavior** of the system.

* Code is authoritative.
* Policy documentation reflects current behavior.
* Tickets exist to change behavior in a controlled, auditable way.

No ticket may silently reinterpret system semantics.

---

## Mandatory Pre-check (Policy-Aware Development)

Before proposing **any** ticket:

1. **Read** the current policy document:

   * `docs/policies/policy-spec.md`

2. Determine whether the issue:

   * already follows existing policy
   * violates existing policy
   * requires a policy clarification
   * requires a policy change or extension

If the ticket affects validation, repair, fallback, canonicalization, flags, or decision routing behavior,
the policy document **must be updated in the same ticket**.

---

## Investigation Step (Recommended for Backend Issues)

Before proposing a backend behavior change:

* The architect may issue a **read-only Codex investigation task** to:

  * trace where a failure code is emitted
  * identify decision escalation paths
  * locate canonicalization logic
  * confirm invariant compliance
  * identify authoritative trigger conditions

Investigation output must:

* cite file paths and functions
* describe trigger conditions clearly
* distinguish between policy and implementation

Investigation does not change behavior.
Behavior changes require a ticket.

---

## Canonicalization vs Ontology Rule (v1.4)

When proposing tickets related to normalization:

* Determine whether the issue belongs in:

  * deterministic canonicalization layer, or
  * ontology grounding logic

Canonicalization must:

* precede ontology grounding
* be deterministic
* not rely on LLM repair
* be documented in `policy-spec.md`

Ontology grounding must:

* validate and normalize
* not introduce inference
* not compensate for missing canonicalization

Tickets must explicitly state which layer is being modified.

---

## UI vs Backend Scope Check

Before proposing a UI-related ticket, explicitly determine scope.

### UI-only tickets MAY:

* Change presentation, layout, navigation, or ergonomics
* Improve transparency of backend artifacts
* Persist explicit curator actions (overrides, checked markers)
* Export derived artifacts from existing backend outputs
* Support explicit, reversible bulk actions initiated by the curator

### UI tickets MUST NOT:

* Re-run backend validation, repair, or ontology grounding
* Reinterpret backend flags or confidence levels
* Synthesize new diagnostic signals
* Infer correctness across GSMs
* Propagate values across GSMs implicitly
* Introduce learning from curator edits
* Compensate silently for backend limitations

If backend behavior would need to change, stop and propose a backend ticket.

---

## Evidence and Diagnostics Rule

For UI tickets involving diagnostics or highlighting:

* `evidence.jsonl` is the sole authoritative source for per-field diagnostics
* UI must not invent, summarize, or reinterpret signals
* Cell highlighting is permitted only if:
  `evidence_by_field[field].flags` is non-empty
* Fallback states are informational only unless explicitly flagged

Any UI ticket violating this must be rejected.

---

## Bulk Actions and Safety Requirements

Tickets proposing bulk operations must explicitly state:

* What is being applied (single column, single value)
* The selection scope (explicit row selection only)
* Preview behavior before apply
* Reversibility guarantees
* Validation or safety checks reused from single-edit semantics

Implicit or automatic bulk operations are prohibited.

---

## Placeholder and Sentinel Rules

The system recognizes canonical sentinel values:

* `"Healthy"` — biologically healthy state
* `"Unknown"` — missing or unspecified value

Tickets must not introduce new sentinel strings.

If a new placeholder form is encountered (e.g., "Not Available", "NA (Healthy Donors)"),
it must be mapped deterministically into existing canonical sentinels.

Ontology grounding must not be used to repair placeholder semantics.

---

## Policy-Related Tickets (Required Rule)

If a ticket:

* introduces a new rule
* changes decision logic
* alters validation, repair, fallback, canonicalization, or flag behavior
* changes ontology preference or interpretation
* changes the meaning of output fields

Then the ticket **must include**:

* a section titled **“Policy Impact”**
* an explicit instruction to update `docs/policies/policy-spec.md`

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

## Layer Affected

- [ ] Canonicalization
- [ ] Ontology grounding
- [ ] Validation / Repair
- [ ] Decision routing
- [ ] UI only
- [ ] Documentation only

## Policy Impact

- [ ] No policy change
- [ ] Policy clarification only
- [ ] Policy change (policy-spec.md must be updated)

## Acceptance Criteria

Objective, testable conditions for completion.

## Non-Goals

What this ticket explicitly does NOT address.

## Constraints

- Do not invent future behavior without evidence.
- Prefer deterministic rules over additional LLM calls.
- Prefer canonicalization over ontology fallback when appropriate.
- Prefer flagging over silent correction when ambiguity is high.
- Human curation must remain explicit and auditable.

## Guiding Principle

Policies are written consequences of code, not aspirations.  
If behavior changes, policy documentation must change with it.

## Ticket File Requirement (MANDATORY)

Create `docs/tickets/ticket-XX.md` and paste this ticket verbatim.
```

---

## Final Rule

When uncertain:

* Investigate first.
* Propose minimal deterministic change.
* Preserve invariants.
* Update policy if semantics change.
* Never introduce silent behavior drift.

The goal is stable evolution under explicit architectural control.
