# Ticket #187: Normalize compound healthy placeholders (e.g., "NA (Healthy Donors)") to "Healthy"

## Background

Observed disease value:
"NA (Healthy Donors)"

Semantics:
- Placeholder prefix ("NA")
- Explicit healthy biological context ("Healthy Donors")

Correct canonical disease value:
"Healthy"

Current behavior may:
- Miss healthy normalization
- Miss placeholder normalization
- Trigger unnecessary ontology grounding and FLAGGED decision

## Problem Statement

Compound disease strings that include both:
- placeholder markers (NA, Unknown, Not Available)
- explicit healthy context

are not deterministically normalized to "Healthy".

This causes incorrect ontology attempts and unnecessary curator flags.

## Proposed Change

Enhance disease canonicalization logic:

### Step Order (must be enforced)

1) Healthy normalization
2) Placeholder normalization
3) Ontology grounding

### Healthy normalization rule

If normalized disease string contains strong healthy indicators such as:

- "healthy donor"
- "healthy donors"
- "healthy control"
- "healthy controls"
- "normal donor"
- "normal healthy"

OR matches pattern:

- placeholder marker + any text containing "healthy"

Then canonicalize to:

- "Healthy"

### Placeholder fallback (unchanged)

If no healthy indicator and placeholder detected:
- canonicalize to "Unknown"

## Policy Impact

[x] Policy update required.

Update policy-spec.md:

- Define compound healthy placeholder normalization rule.
- Clarify precedence: Healthy normalization overrides placeholder fallback.

No whitepaper change required.

## Acceptance Criteria

1) disease = "NA (Healthy Donors)"
   → final_output.disease = "Healthy"
   → no ontology_low_confidence_disease
   → no repair attempts

2) disease = "Unknown healthy controls"
   → final_output.disease = "Healthy"

3) disease = "Not Available"
   → final_output.disease = "Unknown"

4) Determinism preserved across reruns.

5) No regression in mesothelioma rule (#184) or placeholder rule (#185).

## Non-Goals

- No change to ontology ingestion.
- No UI changes.
- No decision-table severity change.

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-187.md` and paste this ticket verbatim.
