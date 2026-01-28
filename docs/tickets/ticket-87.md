# Ticket #87: Deterministic Fallback for Non-Anatomical `tissue_type` Values (e.g. "Tumor")

## Milestone
v0.9 — Validation, Repair, and Reporting Consolidation

## Type
Policy clarification / deterministic fallback logic

## Status
Proposed (policy-level)

---

## Summary

Introduce a deterministic, non-repairing fallback policy for cases where the LLM outputs **non-anatomical placeholders** (e.g. `"Tumor"`) in the `tissue_type` field.

Such values are semantically invalid for `tissue_type` and must not trigger ontology grounding or repair. Instead, they should result in a conservative fallback with a curator-visible informational flag.

---

## Motivation

In many cancer datasets (e.g. CT26 mouse tumor models), GEO metadata and associated papers frequently describe samples only as “tumor” without specifying an anatomical site.

In these cases:
- `"Tumor"` is **not an anatomical tissue**
- Uberon ontology grounding is inappropriate and guaranteed to fail
- Repair loops cannot succeed
- Treating this as `ontology_low_confidence_tissue_type` produces noise

The system should handle this pattern deterministically and transparently.

---

## Policy Definition (Authoritative)

### Non-Anatomical `tissue_type` Placeholder Rule

When **all** of the following conditions hold:

1. Field is `tissue_type`
2. Raw value is a **non-anatomical placeholder**, including but not limited to:
   - `"Tumor"`
   - `"Tumour"`
   - `"tumor tissue"`
   - `"tumor sample"`
3. No anatomical tissue site can be deterministically inferred from context

Then:

- Canonical `tissue_type` MUST be set to `"Unknown"`
- Ontology grounding MUST be skipped for this field
- Repair MUST NOT be attempted for this field
- A curator-visible **informational flag** MUST be emitted
- Final decision MUST remain `FLAGGED` or equivalent non-accept state per existing semantics

This rule is deterministic and conservative.

---

## Flag Semantics

### Flag name
`tissue_type_non_anatomical_placeholder`

### Flag meaning (curator-facing)
> A non-anatomical placeholder (e.g. "tumor") was provided for tissue_type.  
> No anatomical tissue site could be determined automatically.

### Flag properties
- Informational
- Non-fatal
- Non-repair-triggering

---

## Canonical vs Audit Behavior

| Aspect | Behavior |
|------|---------|
| `final_output.tissue_type` | `"Unknown"` |
| Ontology grounding | Skipped |
| Repair attempts | None |
| Audit trail | Original raw value preserved |
| Curator visibility | Flag only |

---

## Scope

IN SCOPE:
- `tissue_type` validation and decision routing
- Deterministic fallback logic
- Flag emission and rationale clarity

OUT OF SCOPE:
- Prompt changes
- Ontology expansion
- Schema changes
- UI changes
- Automatic inference of anatomical site
- Disease or cell lineage policies

---

## Implementation Notes (Non-Prescriptive)

- Detect placeholder values before ontology grounding
- Maintain an explicit allowlist of non-anatomical placeholders
- Bypass both ontology validation and repair for this case
- Ensure behavior is field-local and does not affect other fields

---

## Tests to Add

- Input with `tissue_type = "Tumor"` and no anatomical context:
  - `final_output.tissue_type == "Unknown"`
  - Flag `tissue_type_non_anatomical_placeholder` present
  - No ontology attempts
  - No repair attempts
- Ensure existing behavior unchanged for valid anatomical tissues
- Ensure no interaction with disease or format validation

---

## Non-Goals

This ticket does NOT:
- Infer anatomical sites automatically
- Introduce compound tissue labels
- Change final decision semantics globally
- Modify disease or treatment handling
- Reinterpret “tumor” as an ontology tissue

---

## Rationale

“Tumor” describes pathological status, not anatomy.  
Replacing it with `"Unknown"` while explicitly flagging the reason preserves correctness, transparency, and curator trust without inventing unsupported structure.

---

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-87.md` and paste this ticket verbatim.
