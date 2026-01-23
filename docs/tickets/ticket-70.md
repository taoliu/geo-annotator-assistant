# Ticket #70: Normalize disease query strings by stripping leading model/cell identifiers (e.g. “5TGM1”) before ontology grounding

## Problem

Disease strings sometimes include leading model/cell identifiers (e.g. “5TGM1 multiple myeloma”).
This prevents deterministic exact/synonym ontology matches and results in LOW_CONFIDENCE fuzzy matches (e.g. DOID “multiple myeloma” at jaccard 0.6667) even though the underlying disease term is present.

This is a normalization issue, not an inference issue.

## Scope (minimal, deterministic)

Add a deterministic normalization step for the disease ontology *query string* (not the final output schema):

* If the first token contains digits (e.g. “5TGM1”) and removing it yields a shorter phrase that can be matched deterministically, strip that leading token for ontology matching.
* Apply this only to ontology lookup inputs; do not change the 8-field output schema or introduce new fields.

Ensure the audit artifact records:
* the original raw_value
* the normalized query used for matching (in an existing suitable field if available; otherwise include it in a deterministic, structured way within the ontology match record without changing final output schema)

No changes to:
* decision routing
* scoring thresholds
* repair logic
* schema

## Acceptance Criteria

1. For raw disease value “5TGM1 multiple myeloma”, ontology grounding produces a terminal exact match to “multiple myeloma” (DOID or NCIT) with score 1.0 and status MATCHED.
2. The final output disease is canonicalized to “multiple myeloma” (or the ontology’s canonical label) as permitted by terminal exact semantics.
3. Behavior remains deterministic and auditable.

## Required Tests

Add a regression test for disease grounding:
* input disease = “5TGM1 multiple myeloma”
* assert the ontology match is terminal exact (score 1.0, exact match type)
* assert the selected canonical label is “multiple myeloma” (or equivalent canonical label)
* run `uv run pytest -q`

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-70.md` and paste this ticket verbatim.
