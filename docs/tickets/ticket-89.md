# Ticket #89: Deterministic Handling of Model-Based Disease Identifiers (e.g. CT26)

## Milestone
v0.9 — Validation, Repair, and Reporting Consolidation

## Type
Policy clarification / deterministic fallback logic

## Status
Proposed (policy-level)

---

## Summary

Introduce a deterministic policy for **model-based disease identifiers** (e.g. `CT26 mouse tumor model`) that are experimental system labels rather than pathological disease terms.

Such values MUST NOT be forced through disease ontology grounding or repair. When no ontology-supported disease can be deterministically extracted, the canonical disease value MUST fall back conservatively with a curator-visible informational flag.

---

## Motivation

Cancer GEO datasets frequently encode experimental tumor models in the disease slot, including:

- CT26 mouse tumor model
- MC38 syngeneic tumor model
- B16 melanoma model
- 4T1 breast cancer model
- LLC

These strings describe **experimental models**, not diseases. DOID and NCIT are not designed to represent such model identifiers, so grounding and repair are guaranteed to fail and create noise.

This ticket formalizes correct handling to preserve correctness and curator trust.

---

## Policy Definition (Authoritative)

### Model-Based Disease Identifier Rule

When **all** of the following conditions hold:

1. Field is `disease`
2. Raw disease value matches a **known experimental model pattern**, including:
   - common model identifiers (e.g. CT26, MC38, B16, 4T1, LLC)
   - phrases such as:
     - "mouse tumor model"
     - "syngeneic tumor model"
     - "xenograft model"
3. No explicit, ontology-groundable pathological disease term is present in the value

Then:

- Canonical `disease` MUST be set to `"Unknown"`
- Ontology grounding MUST be skipped for this field
- Repair MUST NOT be attempted for this field
- A curator-visible **informational flag** MUST be emitted
- Final decision MUST remain `FLAGGED` or equivalent non-accept state per existing semantics

This rule is deterministic and conservative.

---

## Flag Semantics

### Flag name
`disease_model_identifier_not_ontology`

### Flag meaning (curator-facing)
> Disease value describes an experimental tumor model (e.g. CT26) rather than a pathological disease term. No ontology-supported disease could be determined automatically.

### Flag properties
- Informational
- Non-fatal
- Non-repair-triggering

---

## Canonical vs Audit Behavior

| Aspect | Behavior |
|------|---------|
| `final_output.disease` | `"Unknown"` |
| Ontology grounding | Skipped |
| Repair attempts | None |
| Audit trail | Original raw value preserved |
| Curator visibility | Flag only |

---

## Scope

IN SCOPE:
- Disease field validation and routing
- Deterministic model detection
- Fallback and flag emission

OUT OF SCOPE:
- Ontology expansion
- Mapping model identifiers to diseases
- Automatic disease inference from model names
- Schema changes
- UI changes
- Prompt changes

---

## Implementation Notes (Non-Prescriptive)

- Use a deterministic allowlist of known model identifiers and phrases
- Detection must be explicit; avoid fuzzy NLP heuristics
- Ensure this rule executes **before ontology grounding and repair**
- Preserve original raw disease string in audit records

---

## Tests to Add

- Input with `disease = "CT26 mouse tumor model"`:
  - `final_output.disease == "Unknown"`
  - Flag `disease_model_identifier_not_ontology` present
  - No ontology attempts
  - No repair attempts
- Ensure existing behavior unchanged when a true disease term is present
- Ensure no interaction with tissue or format handling

---

## Non-Goals

This ticket does NOT:
- Treat model identifiers as diseases
- Invent ontology mappings
- Replace disease with `"Healthy"`
- Infer disease from cell line names
- Modify treatment or tissue logic

---

## Rationale

Experimental model identifiers encode how a tumor was generated, not what disease it represents.  
Replacing them with `"Unknown"` while explicitly flagging the reason preserves accuracy, avoids ontology misuse, and maintains curator trust.

---

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-89.md` and paste this ticket verbatim.
