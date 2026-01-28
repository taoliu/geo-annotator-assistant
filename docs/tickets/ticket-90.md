# Ticket #90: Deterministic Generalization of Human “<site> Tumor” Disease Labels to “<site> Cancer”

## Milestone
v0.9 — Validation, Repair, and Reporting Consolidation

## Type
Policy consolidation / deterministic normalization (disease)

## Status
Proposed (policy-level)

---

## Summary

Introduce a deterministic normalization policy for **sloppy human disease labels** of the form **“<anatomical site> tumor”** (e.g. “Lung Tumor”) to a canonical, ontology-groundable disease label **“<site> cancer”** (e.g. “lung cancer”), when supported by consistent site evidence.

This avoids unnecessary LLM repair loops and reduces curator noise from repeated `ontology_low_confidence_disease` failures caused by non-ontology phrasing.

---

## Motivation

GEO submitters frequently use non-ontology, underspecified disease phrases such as “Lung Tumor” in human datasets. The LLM reproduces these phrases faithfully, but ontology grounding yields LOW_CONFIDENCE and triggers repair loops that often do not converge.

In many cases, the anatomical site is already clearly present and ontology-grounded (e.g. `tissue_type = lung`). For human samples, “<site> tumor” is typically intended as “<site> cancer” in GEO cancer studies and should be canonicalized deterministically.

---

## Policy Definition (Authoritative)

### Human “<site> tumor” → “<site> cancer” Rule

When **all** of the following conditions hold:

1. Field is `disease`
2. `organism` is exactly `Homo sapiens`
3. `tissue_type` is ontology-grounded to an anatomical site (Uberon), and is terminal/locked
4. Raw disease value matches a sloppy tumor pattern equivalent to:
   - `"<site> tumor"` or `"<site> tumour"`
   - `"tumor of <site>"` or `"tumour of <site>"`
   (case-insensitive; hyphen/space normalized)
5. The `<site>` in the disease string is consistent with the grounded `tissue_type` site label (normalized)
6. No model-based tokens are present in disease (must not overlap with Ticket #89 patterns), including but not limited to:
   - known model identifiers (e.g. CT26, MC38, B16, 4T1, LLC)
   - phrases like “mouse model”, “syngeneic”, “xenograft”

Then:

- Canonical disease string MUST be rewritten deterministically to: `"<site> cancer"`
- Ontology grounding MUST be attempted on the rewritten disease using existing DOID + NCIT rules
- Repair MUST NOT be triggered for the original sloppy label
- If ontology grounding succeeds, the disease field MUST be terminally locked to the selected ontology term
- An informational flag MUST be emitted to preserve transparency

If any condition fails, existing v0.8/v0.9 behavior remains unchanged (including Ticket #89 for model-based strings).

---

## Flag Semantics

### Flag name
`disease_generalized_from_sloppy_tumor_label`

### Flag meaning (curator-facing)
> Disease label was a non-ontology phrase of the form “<site> tumor” in a human sample and was generalized deterministically to “<site> cancer” based on matching anatomical site evidence.

### Flag properties
- Informational
- Non-fatal
- Non-repair-triggering

---

## Canonical vs Audit Behavior

| Aspect | Behavior |
|------|---------|
| `final_output.disease` | generalized disease (e.g. `lung cancer`) if grounded; otherwise follow existing rules |
| Ontology grounding | performed on generalized string using DOID + NCIT |
| Repair attempts | none for this pattern |
| Audit trail | original raw disease phrase preserved in audit (`raw_value`, `llm_parsed_outputs`) |
| Curator visibility | informational flag |

---

## Scope

IN SCOPE:
- Disease normalization prior to ontology grounding/repair triggering
- Deterministic site consistency check using already-grounded `tissue_type`
- DOID + NCIT grounding on the rewritten label
- Flag emission

OUT OF SCOPE:
- Inferring disease when site is missing
- Generalizing “tumor” without site evidence
- Guessing histology/subtype (adenocarcinoma, etc.)
- Any LLM-based re-asking/repair for this pattern
- Schema changes
- UI changes

---

## Implementation Notes (Non-Prescriptive)

- Implement as a small pre-grounding normalization step for `disease`
- Require `tissue_type` lock/terminal match before applying
- Apply before ontology grounding and before repair triggering
- Ensure Ticket #89 model-based detection takes precedence (i.e. do not generalize model strings)

---

## Tests to Add

1. Positive case (based on reference audit pattern):
   - organism: `Homo sapiens`
   - tissue_type: `lung` (Uberon exact)
   - disease raw: `Lung Tumor`
   - expected:
     - final disease: `lung cancer`
     - disease grounded to DOID/NCIT (prefer existing selection rules)
     - flag `disease_generalized_from_sloppy_tumor_label` present
     - no disease repair attempts

2. Negative cases:
   - organism not human (e.g. mouse) → rule not applied
   - disease = `Tumor` (no site) → rule not applied
   - tissue_type not grounded/locked → rule not applied
   - disease contains model tokens (CT26, etc.) → defer to Ticket #89 behavior

---

## Non-Goals

This ticket does NOT:
- Create ontology synonyms
- Expand disease ontologies
- Perform fuzzy inference from context text
- Overrule Ticket #89 model-based handling
- Convert benign tumors to cancer without the defined conditions

---

## Rationale

This policy is conservative, deterministic, and curator-aligned. It uses explicit site consistency and human-only scope to avoid overgeneralization while eliminating common low-value FLAGGED outcomes caused by sloppy “<site> tumor” disease labels.

---

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-90.md` and paste this ticket verbatim.
