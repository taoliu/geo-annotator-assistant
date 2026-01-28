# Ticket #92: Deterministic Normalization of Healthy / Control Disease Phrases to Terminal `Healthy`

## Milestone
v0.9 — Validation, Repair, and Reporting Consolidation

## Type
Policy clarification / deterministic normalization (disease)

## Status
Proposed (policy-level)

---

## Summary

Introduce a deterministic normalization policy that maps common **healthy / control subject phrases** (e.g. “Healthy Donors”) in the `disease` field to the terminal canonical value **`Healthy`**.

This prevents unnecessary ontology failures, repair attempts, and persistent FLAGGED records for datasets that explicitly describe healthy or control subjects.

---

## Motivation

GEO metadata frequently uses non-ontology phrases such as:

- “Healthy Donors”
- “Healthy Controls”
- “Normal Donors”
- “Normal Controls”

These phrases are **not diseases**, but clearly indicate the **absence of disease**. The system already allows `Healthy` as a terminal disease value, but currently fails to normalize these common variants, leading to:

- `ontology_low_confidence_disease`
- `disease_inferred_without_evidence`
- ineffective LLM repair attempts
- unnecessary curator review

This ticket formalizes correct, deterministic handling.

---

## Policy Definition (Authoritative)

### Healthy / Control Disease Normalization Rule

When **all** of the following conditions hold:

1. Field is `disease`
2. Raw disease value matches a healthy/control pattern, including but not limited to:
   - “healthy donor”
   - “healthy donors”
   - “healthy control”
   - “healthy controls”
   - “normal donor”
   - “normal donors”
   - “normal control”
   - “normal controls”
   (case-insensitive; singular/plural normalized)
3. The phrase refers to **subject health status**, not an intervention or treatment context

Then:

- Canonical disease MUST be set to `Healthy`
- The disease field MUST be treated as terminal
- Ontology grounding MUST be skipped for this field
- LLM repair MUST NOT be triggered
- Existing semantic error `disease_inferred_without_evidence` MUST NOT be raised
- An informational flag MAY be emitted for transparency

---

## Flag Semantics

### Optional curator-visible flag name
`disease_normalized_to_healthy`

### Flag meaning (curator-facing)
> Disease label indicated healthy/control subjects and was normalized to the terminal value “Healthy”.

### Flag properties
- Informational
- Non-fatal
- Non-repair-triggering

(Flag emission may be optional; normalization must occur regardless.)

---

## Canonical vs Audit Behavior

| Aspect | Behavior |
|------|---------|
| `final_output.disease` | `Healthy` |
| Ontology grounding | Skipped |
| Repair attempts | None |
| Audit trail | Original raw disease phrase preserved |
| Final decision | MAY be `ACCEPT` if no other blocking failures exist |

---

## Scope

IN SCOPE:
- Disease normalization logic
- Deterministic handling of healthy/control phrases
- Repair boundary enforcement
- Flag emission semantics

OUT OF SCOPE:
- Inferring disease from treatment
- Mapping ambiguous “control” usage without context
- Ontology expansion
- Schema changes
- UI changes

---

## Implementation Notes (Non-Prescriptive)

- Implement normalization before ontology grounding and before semantic error checks
- Maintain a clear allowlist of healthy/control phrases
- Ensure this rule takes precedence over `disease_inferred_without_evidence`
- Ensure compatibility with existing terminal `Healthy` semantics defined in v0.8

---

## Tests to Add

1. Positive cases:
   - `disease = "Healthy Donors"` → `final_output.disease == "Healthy"`
   - `disease = "Normal Controls"` → `final_output.disease == "Healthy"`
   - No ontology attempts, no repair attempts, no semantic errors

2. Negative cases:
   - `disease = "Control treatment"` → rule not applied
   - `disease = "tumor control arm"` → rule not applied
   - `disease = "healthy tissue adjacent to tumor"` → rule not applied

---

## Non-Goals

This ticket does NOT:
- Guess disease when unclear
- Replace disease based on treatment or tissue
- Alter treatment handling
- Expand disease vocabulary beyond `Healthy`
- Override model-based disease handling (Ticket #89)

---

## Rationale

Healthy/control phrases describe subject status, not pathology.  
Normalizing them deterministically to `Healthy` aligns system output with curator expectations, reduces noise, and preserves correctness without LLM guessing.

---

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-91.md` and paste this ticket verbatim.
