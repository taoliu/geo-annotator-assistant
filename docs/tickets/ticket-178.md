# Ticket #178: Fix NCIT synonym exact matching for disease (parse JSON-string synonyms)

## Background

Case: GSE184398 / GSM5586284

LLM disease: "Gynecologic cancer"

Audit shows disease ontology match:
- selected_source = "NCI Thesaurus"
- status = LOW_CONFIDENCE
- match_type = token_equiv_similarity
- alternates do not include NCIT:C4913

However, ontology Chroma DB contains:
- NCIT:C4913 "Malignant Female Reproductive System Neoplasm"
- synonyms include "gynecologic cancer" (exact)

Direct DB inspection confirms:
- metadata["synonyms"] is stored as a JSON-encoded string, not a list
- parsing reveals "gynecologic cancer" is present

Therefore, the NCIT synonym exact matching path is skipping synonyms due to incorrect type handling.

## Problem Statement

NCIT disease grounding fails to perform deterministic synonym exact matching because
the synonyms metadata is stored as a JSON string and is not parsed before matching.
This causes the system to fall back to similarity matching and incorrectly return
LOW_CONFIDENCE results, leading to unnecessary repair attempts and FLAGGED outputs.

## Proposed Change

In the NCIT ontology matcher (disease field):

1) When reading synonyms from metadata:
   - If `synonyms` is a string, parse it via `json.loads(synonyms)`
   - If `synonyms` is already a list, use as-is
   - If missing/null, treat as empty list

2) Ensure synonym normalization matches label/query normalization:
   - casefold/lowercase
   - normalize whitespace
   - normalize hyphen vs space consistently (use the same existing normalizer)

3) After failing label_norm_exact, attempt synonym_norm_exact deterministically:
   - If query matches any normalized synonym:
       - status = MATCHED
       - matched_term_id = that term_id
       - matched_label = preferred label
       - matched_source = "NCI Thesaurus"
       - match_type = synonym_norm_exact (or existing synonym exact enum)
       - matched_via = synonym_norm (or existing field)
       - skip vector fallback for this case

No new LLM calls.

## Policy Impact

No policy change expected.
This is a correctness fix to align implementation with existing policy intent:
exact synonyms must match deterministically when present.

## Acceptance Criteria

1) GSM5586284 (GSE184398):
   - disease resolves as MATCHED to NCIT:C4913
   - matched_label = "Malignant Female Reproductive System Neoplasm"
   - match_type indicates synonym exact (not similarity)
   - no ontology_low_confidence_disease flag
   - no repair attempts consumed for disease
   - final_decision is no longer FLAGGED due to disease

2) Determinism preserved across reruns.

3) Regression checks:
   - NCIT exact label matches unchanged
   - similarity fallback unchanged when no exact synonym exists
   - DOID behavior unchanged

## Implementation Hint (non-normative)

In the synonym-handling block:

- `syn = md.get("synonyms", [])`
- if `isinstance(syn, str)`: `syn = json.loads(syn)`
- then proceed as list

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-178.md` and paste this ticket verbatim.
