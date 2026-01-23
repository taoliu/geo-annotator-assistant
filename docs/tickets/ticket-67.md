# Ticket #67: Fix NCIT trigger coverage for plural and morphological disease terms (e.g. “malignancies”)

## Problem

Certain disease phrases (e.g. “B cell malignancies”) fail to trigger NCIT lookup even though NCIT contains an exact or near-exact corresponding term (“B-Cell Malignant Neoplasm”, synonym “B-Cell Malignancy”).

Audit shows NCIT triggering is gated by a fixed list of lexical substrings (e.g. “malignan”), which may not match common plural or morphological variants (e.g. “malignancies”).

As a result, ontology grounding falls back to low-confidence DOID matches instead of a deterministic NCIT match.

## Scope (minimal, deterministic)

Improve NCIT trigger detection to correctly fire on common morphological variants of existing trigger terms, including but not limited to:

* malignancy / malignancies
* plural forms of existing trigger words

This may be implemented via:
* simple token normalization, or
* explicit addition of missing variants

No changes to:
* ontology scoring thresholds
* decision routing
* canonicalization rules
* repair logic
* schema

## Acceptance Criteria

1. For input disease value “B cell malignancies”:
   * NCIT lookup is deterministically triggered.
   * NCIT term “B-Cell Malignant Neoplasm” (or equivalent) appears as a candidate with high confidence.
2. Ontology grounding behavior remains deterministic and auditable.
3. No change to ACCEPT/FLAGGED logic unless already implied by existing rules.
4. Existing ontology tests continue to pass.

## Required Tests

Add a regression test where:
* disease = “B cell malignancies”
* NCIT triggering is expected
* audit records show NCIT attempted and candidate returned

Run:
`uv run pytest -q`

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-67.md` and paste this ticket verbatim.
