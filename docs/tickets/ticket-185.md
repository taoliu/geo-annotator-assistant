# Ticket #185: Map disease placeholder "Not Available" to canonical sentinel "Unknown"

## Background

Case: GSE212521 / GSM6533913

LLM disease: "Not Available"

Current behavior:
- "Not Available" is not recognized as a non-answer placeholder
- disease goes through ontology grounding, fails with LOW_CONFIDENCE
- emits ontology_low_confidence_disease
- final_decision = FLAGGED

Codex confirmed a shared placeholder mechanism already exists:

- `is_llm_non_answer_placeholder()` with `_NON_ANSWER_PLACEHOLDERS`
- canonical fallback mapping `_NON_ANSWER_FALLBACKS` maps:
  - disease -> "Unknown"
- ontology validator already treats recognized placeholders as FALLBACK via
  `matched_via="llm_non_answer_placeholder"`
- disease fallback markers are exactly {"Healthy", "Unknown"}

So we should reuse this existing system.

## Problem Statement

The placeholder string "Not Available" is a common missing-value marker in GEO-like metadata
but is not included in `_NON_ANSWER_PLACEHOLDERS`. This causes unnecessary ontology matching,
repair attempts, and misleading ontology_low_confidence_disease failures.

## Proposed Change

1) Extend `_NON_ANSWER_PLACEHOLDERS` to include "not available" variants so that:
   - `disease = "Not Available"` is recognized by `is_llm_non_answer_placeholder()`
   - canonicalization rewrites disease to "Unknown" via existing `_NON_ANSWER_FALLBACKS`

2) Ensure normalization is robust and deterministic:
   - case-insensitive match (casefold)
   - whitespace-normalized match
   - accept common variants:
     - "Not Available"
     - "not available"
     - "Not available"
     - optionally "N/A" if not already present

3) Expected pipeline behavior after change:
   - `final_output.disease` becomes "Unknown"
   - disease ontology matching is marked as FALLBACK with `matched_via="llm_non_answer_placeholder"`
   - No `ontology_low_confidence_disease` should be emitted for this input

Decision semantics:
- Keep existing decision table behavior for disease="Unknown" (do not change in this ticket).
- This ticket only normalizes the placeholder into the existing sentinel.

## Policy Impact

[x] Policy update required (small clarification).

Update policy-spec.md to list "Not Available" as an accepted non-answer placeholder that maps to:
- disease -> "Unknown"

No whitepaper change required.

## Acceptance Criteria

1) Repro case GSM6533913:
- `final_output.disease == "Unknown"`
- disease ontology status is FALLBACK (not LOW_CONFIDENCE)
- `ontology_low_confidence_disease` is not present
- no disease repair attempts triggered for this placeholder case

2) Determinism:
- repeated runs yield identical results.

3) Regression:
- Normal disease strings still go through ontology grounding unchanged.
- "Healthy" normalization unchanged.

## Non-Goals

- No change to decision severities for "Unknown".
- No changes to ingestion tooling.
- No UI changes.

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-185.md` and paste this ticket verbatim.
