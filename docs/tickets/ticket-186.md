# Ticket #186: Normalize "peripheral blood" to "blood" before Uberon grounding

## Background

Observed case:

- tissue_type = "peripheral blood"
- Uberon grounding fails or yields LOW_CONFIDENCE
- This is not an ontology uncertainty issue
- It is a deterministic terminology normalization issue

In practice, "peripheral blood" in GEO metadata refers to circulating blood
and should be canonicalized to the Uberon term:

- "blood" (UBERON:0000178)

Uberon does not consistently model "peripheral blood" as a primary label,
so attempting direct grounding causes unnecessary repair attempts and flags.

## Problem Statement

The current pipeline treats "peripheral blood" as a free-text anatomical term.
Because it does not map directly to a primary Uberon label,
it may trigger LOW_CONFIDENCE or repair loops.

This is a deterministic normalization case, not a curator-required ambiguity.

## Proposed Change

Add a pre-grounding canonical rewrite rule for tissue_type:

If normalized tissue_type equals:

- "peripheral blood"

Rewrite deterministically to:

- "blood"

Then proceed with standard Uberon grounding.

### Normalization Rules

- case-insensitive (casefold)
- whitespace-normalized
- exact match only (do not substring-match)

No LLM call required.
No ontology fallback required.

## Optional (if desired)

If you want slightly broader normalization, also allow:

- "whole blood" → "blood"

But do NOT rewrite:
- "PBMC"
- "peripheral blood mononuclear cells"
- "bone marrow blood"

Those should remain distinct and handled separately.

## Policy Impact

[x] Policy update required.

Update policy-spec.md:

- Define deterministic tissue canonicalization rule:
  - "peripheral blood" → "blood"
- Clarify that this rewrite occurs before ontology grounding.

No whitepaper change required.

## Acceptance Criteria

1) For any sample with tissue_type = "peripheral blood":
   - final_output.tissue_type == "blood"
   - Uberon match status = MATCHED
   - matched_term_id = UBERON:0000178
   - no ontology_low_confidence_tissue_type
   - no repair attempts triggered

2) Determinism:
   - repeated runs produce identical output.

3) Regression:
   - PBMC remains unaffected.
   - Composite tissue logic (#176) unaffected.
   - Other tissues unaffected.

## Non-Goals

- No ontology ingestion changes.
- No vector matching changes.
- No UI changes.

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-186.md` and paste this ticket verbatim.
