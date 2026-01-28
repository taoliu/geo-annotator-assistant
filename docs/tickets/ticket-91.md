# Ticket #91: Make `treatment_identity_leakage` a Deterministic, Non-Repairing Fallback (Option B)

## Milestone
v0.9 — Validation, Repair, and Reporting Consolidation

## Type
Policy clarification / repair boundary hardening / reporting semantics

## Status
Proposed (policy-level)

---

## Summary

Redefine `treatment_identity_leakage` as a **deterministic, non-repairing semantic condition** rather than a repair-triggering failure.

When detected, the system MUST:
- deterministically set `treatment = None`
- skip the LLM repair loop entirely
- emit a curator-visible **informational flag** indicating that the provided value was not a true treatment

This change eliminates spurious `repair_template_missing` flags and aligns treatment handling with v0.9 repair boundaries.

---

## Motivation

In real-world GEO scRNA-seq datasets, the `treatment` field frequently contains:

- cell subset labels (e.g. “T and NK cell subset”)
- sample or timepoint identifiers (e.g. “PT1_early_CD3”)
- grouping or stratification metadata

These values are **not treatments**. Attempting LLM repair for such cases is inappropriate and guaranteed to fail or hallucinate.

The current pipeline incorrectly treats `treatment_identity_leakage` as repairable, leading to:
- unnecessary repair attempts
- missing repair templates
- confusing curator-visible flags (`repair_template_missing`)
- otherwise correct records appearing “broken”

---

## Policy Definition (Authoritative)

### Treatment Identity Leakage Rule

When the validator detects `treatment_identity_leakage`:

1. The failure MUST NOT trigger LLM repair.
2. The canonical `treatment` value MUST be set deterministically to `"None"`.
3. The record MUST be allowed to proceed to finalization.
4. A curator-visible informational flag MUST be emitted.
5. The record MAY be ACCEPTED if no other blocking failures exist.

---

## Flag Semantics

### Curator-visible flag name
`treatment_not_an_intervention`

### Flag meaning (curator-facing)
> The provided treatment value describes a sample identity, subset, or grouping rather than an experimental intervention. The treatment field was set to None.

### Flag properties
- Informational
- Non-fatal
- Non-repair-triggering

### Explicitly disallowed
- `repair_template_missing` MUST NOT be emitted as a result of `treatment_identity_leakage`.

---

## Required Behavior Changes

1. **Repair boundary update**
   - Remove `treatment_identity_leakage` from the set of repair-triggering failure codes.

2. **Deterministic fallback**
   - Upon detection, directly set `treatment = None`.

3. **Flag routing**
   - Emit `treatment_not_an_intervention` as a curator-visible informational flag.
   - Keep internal detection details in audit logs only.

4. **Final decision logic**
   - Records with only this condition MAY be `ACCEPT`.

---

## Scope

IN SCOPE:
- Validation → repair routing logic
- Treatment field fallback behavior
- Flag semantics and visibility
- Final decision consistency

OUT OF SCOPE:
- LLM prompt changes
- Ontology changes
- Treatment ontology expansion
- Schema changes
- UI changes

---

## Implementation Notes (Non-Prescriptive)

- Handle `treatment_identity_leakage` similarly to other deterministic semantic fallbacks (e.g. Tickets #87, #89).
- Ensure repair loop is not entered for this failure code.
- Ensure `repair_history` is empty for treatment in this case.

---

## Tests to Add

1. Input with treatment value containing subset / identity labels:
   - Expected:
     - `final_output.treatment == "None"`
     - Flag `treatment_not_an_intervention` present
     - No repair attempts
     - No `repair_template_missing` anywhere in output

2. Ensure behavior unchanged when:
   - treatment is a real intervention (e.g. “PD-1 blockade”)
   - treatment field is already `None`

---

## Non-Goals

This ticket does NOT:
- Attempt to infer or hallucinate treatments
- Convert identity labels into interventions
- Change treatment schema or vocabulary
- Affect disease or tissue handling
- Modify audit log structure beyond routing

---

## Rationale

A value that is not a treatment cannot be repaired into one.  
Treating `treatment_identity_leakage` as deterministic rather than repairable eliminates noise, reduces LLM usage, and produces clearer curator-facing annotations.

---

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-91.md` and paste this ticket verbatim.
