# Ticket #20: AGENT-WS-020 — Synonym-aware ontology grounding (deterministic reranking + audit enrichment)

You are working in repo `geo-gsm-annotator-agent`.

## Context

Real GEO metadata often uses abbreviations or short forms (for example disease = `CLL`) that may not match ontology labels exactly. However, ontology documents in our ChromaDB include a `synonyms` list in metadata (for example DOID:1040 includes synonym `CLL` for “chronic lymphocytic leukemia”).

We want ontology grounding to deterministically recognize exact synonym matches, improve confidence when appropriate, and record this reasoning in audit output. This should not require rebuilding the ChromaDB index.

## Goal

1. Add synonym-aware deterministic matching on top of existing retrieval results:

   * If the raw value matches a candidate term’s synonym (case-insensitive, normalized), treat as a confident match.
2. Enrich audit outputs to explicitly record whether the match came from a label or a synonym.
3. Keep the existing retrieval mechanism (Chroma query with query_embeddings) unchanged.

## Non-goals

* Do not rebuild the ontology ChromaDB.
* Do not add fuzzy matching against synonyms beyond simple normalization (no edit distance).
* Do not change the 8-field output schema.
* Do not loosen evidence rules (this is only about ontology grounding).

---

## Design requirements

### A) Normalization function (shared)

Implement a small deterministic normalization used for label and synonym comparisons:

* strip whitespace
* lowercase
* collapse internal whitespace to single spaces
* remove trivial punctuation differences (at minimum: `-`, `_`, `/`, `,`, `.`, `:`)
* keep alphanumerics and spaces

This normalization must be local and easy to test.

### B) Synonym-aware match decision

Given the retrieved candidates (each candidate has `label` and possibly `synonyms` in metadata):

* If `normalize(raw_value) == normalize(label)`:

  * set `match_type = "label_exact"`
  * accept with score 1.0
* Else if any synonym satisfies `normalize(raw_value) == normalize(synonym)`:

  * set `match_type = "synonym_exact"`
  * accept with score 1.0
  * record the matched synonym string
* Else:

  * fall back to existing matching logic and confidence rules (do not change them in this ticket)

### C) Audit enrichment

Extend ontology match records to include:

* `matched_via`: `"label"` or `"synonym"` or `null`
* `matched_synonym`: the exact synonym text that matched (or `null`)

These fields should be present for all ontology match records (use null when not applicable) to keep the audit schema stable.

---

## Tasks

### 1) Locate and update ontology matching code path

Likely files (confirm in repo):

* `src/validator/ontology_match.py`
* `src/validator/ontology_validator.py`
* `src/rag/retrieve.py` or `src/rag/candidate.py`

Actions:

* Implement normalization helper in a suitable place (prefer: `src/validator/ontology_match.py` or a small utility module under validator).
* Update the candidate scoring / selection step to apply synonym exact match before any “low confidence” outcome is finalized.

### 2) Ensure alternates still include candidates

Even when synonym exact match is found:

* keep `alternates` populated as before (top-k candidates),
* but the primary match should be marked as matched.

### 3) Add tests

Add tests that do not depend on the real ChromaDB, using the candidate structures directly.

Create:

* `tests/test_ontology_synonym_matching.py`

Test cases:

1. Disease synonym match:

   * raw value `"CLL"`
   * candidate label `"chronic lymphocytic leukemia"`
   * synonyms include `"CLL"`
   * Expected: MATCHED, `match_type="synonym_exact"`, `matched_via="synonym"`, `matched_synonym="CLL"`, score 1.0
2. Label match still works:

   * raw value equals label
   * Expected: `match_type="label_exact"`, `matched_via="label"`
3. Normalization works:

   * raw `"RNA seq"` matches label `"RNA-Seq"` after normalization (if your existing exact match already handles this, ensure the new normalization does not break it)
4. No synonym present:

   * Expected: behavior unchanged (falls back to existing logic)

### 4) Update any audit schema documentation (if present)

If you have a doc describing audit fields, update it. If not, skip.

---

## Acceptance criteria

* `uv run pytest -q` passes.
* When raw value matches a synonym exactly (with normalization), ontology grounding returns `status="MATCHED"` with `match_type="synonym_exact"` and score 1.0.
* Audit ontology match records include `matched_via` and `matched_synonym` keys consistently.
* Existing non-synonym behavior remains unchanged.

---

## Ticket file requirement (MANDATORY)

After writing this ticket content, the AI coding agent must create:

* `docs/tickets/ticket-20.md`

and copy the full contents of this ticket verbatim into that file.

---
