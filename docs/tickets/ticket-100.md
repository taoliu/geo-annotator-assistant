# Ticket #100: v0.9 disease grounding should handle parenthetical acronyms and lymphoid/lymphocytic token equivalence

## Background

Observed in curation.jsonl for:
- GSE112494 / GSM3071332
- disease = "Chronic Lymphoid Leukemia (CLL)"
Final decision FLAGGED due to primary_failure = ontology_low_confidence_disease.

Audit shows NCIT alternates include "Chronic Lymphocytic Leukemia" (NCIT:C3163) at confidence 0.6 via jaccard.

## Problem Statement

A disease string that is effectively a standard ontology concept plus a parenthetical acronym is failing to reach MATCHED, even though an appropriate NCIT concept is present among alternates.

This creates unnecessary FLAGGED outputs for common biomedical strings like "<disease> (ACRONYM)".

## Proposed Change

Deterministic-only improvements (no new LLM calls):

1) Disease query cleaning:
   - When forming the ontology query string for disease grounding, strip trailing parenthetical acronym patterns, e.g.
     "X (CLL)" -> "X"
   - Keep the original raw_value unchanged in audit; store the cleaned query as query_used.

2) Token-equivalence expansion (disease only):
   - Extend existing disease token-equivalence normalization to treat "lymphoid" and "lymphocytic" as equivalent tokens for scoring/matching purposes.
   - This should affect match scoring and may allow token_equiv_similarity to produce MATCHED + lock when thresholds are satisfied.
   - Do not introduce a general text rewrite rule for final outputs beyond existing canonicalization semantics.

## Policy Impact

* [ ] No policy change
* [ ] Policy clarification only
* [x] Policy change (policy-spec.md must be updated)

Update `docs/policies/policy-spec.md`:
- Document the parenthetical acronym stripping behavior for disease ontology queries.
- Document the added lymphoid/lymphocytic token-equivalence in the Ticket #96-style token equivalence section.

## Acceptance Criteria

1) Given raw disease "Chronic Lymphoid Leukemia (CLL)", ontology grounding selects NCIT:C3163 "Chronic Lymphocytic Leukemia" as MATCHED (not LOW_CONFIDENCE).
2) final_decision for this record becomes ACCEPT unless other independent failures remain.
3) Audit records:
   - raw_value remains unchanged
   - query_used reflects the cleaned query
   - matched_term_id and matched_label are populated
   - matched_via indicates token-equivalence or synonym/exact path as applicable
4) Add a unit test reproducing this case.
5) No changes to output schema, repair semantics, decision routing, or UI behavior.

## Non-Goals

- No new disease inference.
- No cross-field or cross-GSM propagation.
- No additional ontology sources.
- No general-purpose acronym expansion beyond stripping parenthetical acronyms from the ontology query string.

## Constraints

- Deterministic only.
- Preserve auditability (record both raw_value and query_used).
- Do not broaden matching in a way that increases false-positive terminal locks.

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-100.md` and paste this ticket verbatim.
