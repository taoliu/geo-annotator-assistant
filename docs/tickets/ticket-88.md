# Ticket #88: Enforce Locked Field Values in Final Output Assembly

## Milestone
v0.9 — Validation, Repair, and Reporting Consolidation

## Type
Correctness bug fix / writer logic hardening

## Status
Proposed (implementation follow-up)

---

## Summary

Fix a writer-stage bug where fields that are **explicitly locked with canonical fallback values** (e.g. `tissue_type = "Unknown"`) are ignored during final output assembly, causing raw LLM values (e.g. `"Tumor"`) to leak into `final_output`.

All locked field values MUST take precedence in final output.

---

## Motivation

After Ticket #87, non-anatomical `tissue_type` placeholders such as `"Tumor"` are:

- correctly detected
- correctly classified as semantic placeholders
- correctly assigned a canonical fallback value (`"Unknown"`)
- correctly recorded in `locked_fields`
- correctly flagged for curators

However, the final output still emits the **raw LLM value** instead of the locked canonical value.

This creates a contradiction between:
- policy decision (`locked_fields`)
- emitted annotation (`final_output`)

and undermines curator trust.

---

## Observed Failure Pattern (Reference Case)

From audit log:

```json
"locked_fields": {
  "tissue_type": {
    "label": "Unknown",
    "reason": "tissue_type_non_anatomical_placeholder",
    "original_value": "Tumor"
  }
}
```

But final output incorrectly shows:

```json
"final_output": {
  "tissue_type": "Tumor"
}
```

This violates the meaning of a locked field.

---

## Policy Definition (Authoritative)

### Locked Field Precedence Rule

For **all fields**:

> If a field appears in `locked_fields`, the value in
> `locked_fields[field].label` MUST be used in `final_output`, regardless of ontology status or term ID.

This applies to:

* ontology terminal locks
* semantic fallback locks
* policy-driven generalizations

---

## Required Behavior Changes

1. **Writer precedence enforcement**

   * During final output assembly:

     * check `locked_fields` first
     * emit `locked_fields[field].label` unconditionally if present

2. **Do not infer from ontology status**

   * `status = FALLBACK` with `term_id = null` MUST NOT imply “use raw value”
   * Locked semantic fallbacks are authoritative

3. **Consistency guarantee**

   * `final_output` MUST be consistent with:

     * `canonicalizations`
     * `locked_fields`
     * decision rationale

---

## Scope

IN SCOPE:

* Final output construction logic
* Writer or equivalent module
* Field value precedence rules

OUT OF SCOPE:

* Validation rules
* Ontology matching
* Repair logic
* Prompt changes
* Schema changes
* UI changes

---

## Implementation Notes (Non-Prescriptive)

* Centralize field resolution logic:

  1. `locked_fields[field]`
  2. canonical ontology value (if matched)
  3. raw LLM value
* Apply uniformly across all fields
* Do not special-case `tissue_type` only

---

## Tests to Add

* Regression test using Ticket #87 pattern:

  * `tissue_type = "Tumor"` → locked to `"Unknown"`
  * Assert `final_output.tissue_type == "Unknown"`
* Test that ontology terminal locks still work
* Test that raw values are only used when no lock exists

---

## Non-Goals

This ticket does NOT:

* Change policy decisions
* Alter which fields are locked
* Modify flag semantics
* Add new fallback rules
* Introduce field-specific hacks

---

## Rationale

A locked field represents a finalized, authoritative decision.
Emitting any other value in final output is a correctness violation.

This fix ensures policy decisions are faithfully reflected in canonical annotations.

---

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-88.md` and paste this ticket verbatim.
