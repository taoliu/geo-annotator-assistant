# Ticket #69: Fix audit serialization of matched_synonym for synonym-based ontology matches

## Problem

In audit.jsonl ontology match records, `matched_synonym` can be emitted with malformed formatting (e.g. a truncated JSON-encoded string like `"[\"B-Cell Malignancy\""`).

This is confusing for curators and breaks downstream parsing expectations for audit artifacts.

## Scope (minimal)

Ensure `matched_synonym` is serialized deterministically in one of these forms:

* a plain string containing the matched synonym (preferred), OR
* a valid JSON list (if multiple synonyms are represented)

The chosen representation must be consistent across ontology sources and match types.

No changes to:
* ontology selection logic
* match scoring
* decision routing
* schema of final 8-field outputs

## Acceptance Criteria

1. For a synonym_exact match (e.g. “B cell malignancies” → NCIT “B-Cell Malignant Neoplasm”), `matched_synonym` is emitted in a valid, consistent format.
2. Existing tests pass.

## Required Tests

Add a regression test that:
* runs disease grounding on “B cell malignancies”
* asserts `matched_synonym` is either a plain string or valid JSON list (no malformed fragments)

Run:
`uv run pytest -q`

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-69.md` and paste this ticket verbatim.
