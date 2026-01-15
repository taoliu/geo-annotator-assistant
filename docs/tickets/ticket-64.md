# Ticket #64: UI-DOC-001 — Curator UI documentation polish and v0.7 behavior clarification

## Background

After v0.7 UI refinements, the curator interface behavior has changed substantially:

* GSM details are modal-based
* Table is the primary navigation surface
* Ontology grounding signals are visible but non-authoritative
* Overrides are session-only with soft safety mechanisms
* No backend behavior is affected by UI actions

Documentation must be updated to prevent misuse, confusion, or incorrect assumptions about persistence, backend logic, or ontology “truth”.

This ticket is documentation-only.

---

## Scope (STRICT)

### In scope

1. **Update `docs/ui.md`**
   Revise the curator UI documentation to reflect v0.7 behavior:

   * How to open GSM details (table → modal)
   * What the Field Status Dashboard shows
   * Meaning of UI badges:

     * LOCKED
     * CANONICALIZED
     * TERMINAL EXACT
     * AMBIGUOUS / NO MATCH
     * OVERRIDDEN
   * Evidence panels:

     * what is shown
     * what is intentionally not shown (no free-text rationale)

2. **Clarify override semantics**
   Explicitly document that:

   * Overrides are session-only
   * Overrides do not retrigger:

     * inference
     * repair
     * ontology grounding
   * Overrides may replace even canonicalized or terminal exact values
   * Exported overrides are explicit input artifacts, not learned state

3. **Clarify ontology confidence vs correctness**
   Add a short explanatory section:

   * Ontology canonicalization ≠ correctness
   * Terminal exact ≠ ground truth
   * Human curator judgment is final

   This must align with the whitepaper’s human override invariants.

4. **Non-goals and guardrails**
   Clearly state what the UI does *not* do:

   * No persistence
   * No learning
   * No backend logic
   * No schema changes
   * No cross-GSM propagation

5. **Screenshots (optional)**

   * If screenshots already exist in the repo, update captions.
   * Do not add new screenshots unless trivial.

---

## Explicitly Out of Scope

* Any code changes
* Any backend or config changes
* Any new features
* Any change to whitepaper, milestones, or checkpoints

---

## Acceptance Criteria

1. `docs/ui.md` accurately reflects the current v0.7 UI behavior.
2. No documentation suggests that:

   * ontology confidence equals correctness
   * overrides persist or retrigger backend logic
3. Documentation tone is precise, neutral, and curator-facing.
4. No other files are modified.

---

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-64.md` and paste this ticket verbatim.

---
