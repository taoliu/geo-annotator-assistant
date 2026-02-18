# Ticket #182: Standardize synonym parsing and exact matching across all ontology sources

## Background

We encountered multiple cases where exact synonym matches failed:

1) NCIT disease:
   - "Gynecologic cancer" should match NCIT:C4913
   - synonyms stored as JSON string
   - synonym exact matching was skipped

2) Cellosaurus cell_line:
   - "H1975" should match CVCL:1511 (NCI-H1975)
   - synonyms stored as JSON string
   - synonym exact matching was skipped

Root cause:
- `metadata["synonyms"]` is stored as a JSON-encoded string
- Matching logic assumes list type and silently skips exact synonym matching

This is not specific to one ontology source.
It is a systemic ingestion/matching inconsistency.

## Problem Statement

Synonym exact matching is inconsistently applied because:

- Some ontology records store `synonyms` as JSON strings.
- Some may store them as lists.
- Matching logic does not normalize type and format before comparison.

This leads to:
- Incorrect LOW_CONFIDENCE matches
- Unnecessary repair loops
- Incorrect FLAGGED decisions
- Repeated ontology-specific fixes

We need a unified solution.

## Proposed Change

### A. Centralized Synonym Normalization Layer

Implement a single normalization function used by all ontology matchers:

Function responsibilities:

1) Read `metadata["synonyms"]`
   - If string → parse via `json.loads`
   - If list → use as-is
   - If null/missing → empty list

2) Normalize each synonym using the same canonical normalizer used for labels:
   - casefold/lowercase
   - whitespace normalization
   - hyphen/space equivalence normalization
   - apply existing compact/space normalization rules consistently

3) Return normalized synonym list.

This function must be used in:

- DOID matcher
- NCIT matcher
- Cellosaurus matcher
- Uberon matcher
- EFO matcher
- Any future ontology sources

No ontology-specific custom parsing allowed.

---

### B. Matching Order (Uniform Across All Sources)

For every ontology source:

1) label_norm_exact
2) synonym_norm_exact
3) other deterministic exact variants (if applicable)
4) similarity / jaccard / vector fallback

If synonym_norm_exact matches:
- status = MATCHED
- match_type = synonym_norm_exact
- matched_via = synonym_norm
- skip similarity fallback

---

### C. Determinism Requirements

- Synonym normalization must be deterministic.
- Order of synonyms must not affect outcome.
- Exact matches must always override similarity-based matches.

---

## Policy Impact

No semantic policy change.
This aligns implementation with existing policy intent:

> Exact synonym matches must resolve deterministically before similarity fallback.

Update `policy-spec.md` to clarify:

- Synonym exact matching is required across all ontology sources.
- Synonyms must be normalized and parsed uniformly.
- JSON-string storage format must not affect matching.

No whitepaper change required.

---

## Acceptance Criteria

### Case 1 — NCIT disease
- "Gynecologic cancer" resolves to NCIT:C4913
- match_type = synonym_norm_exact
- no LOW_CONFIDENCE
- no repair attempts

### Case 2 — Cellosaurus cell_line
- "H1975" resolves to CVCL:1511
- matched_label = "NCI-H1975"
- match_type = synonym_norm_exact
- no repair attempts

### Regression Tests

- Existing label_norm_exact matches unchanged
- Similarity fallback still works when no exact synonym exists
- Composite logic (#176) unaffected
- Determinism preserved across reruns

---

## Non-Goals

- No change to ontology schema
- No change to vector embeddings
- No change to composite resolution logic
- No UI changes

---

## Ticket file requirement (MANDATORY)

Create:

docs/tickets/ticket-182.md

Paste this ticket verbatim.
