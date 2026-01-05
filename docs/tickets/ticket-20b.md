# Ticket #20b: AGENT-WS-020b — Preserve ontology synonyms through candidate construction (fix synonym_exact matching)

You are working in repo `geo-gsm-annotator-agent`.

This ticket is a follow-up to **Ticket #20** in the same Codex session.

## Context

Ticket #20 implemented synonym-aware ontology matching logic (`synonym_exact`) and audit enrichment.
However, testing revealed that although synonyms are present in the ChromaDB metadata, they are **not preserved through candidate construction**, so the matcher never sees them.

Direct Chroma queries confirm that ontology entries (for example DOID:1040) include extensive `synonyms`, including `"CLL"`, but these are dropped before matching.

As a result:

* `CLL` fails to match `chronic lymphocytic leukemia`
* audit shows `LOW_CONFIDENCE` instead of `MATCHED`
* `matched_via` and `matched_synonym` remain null

This is a propagation bug, not a retrieval or matching bug.

## Goal

Ensure ontology synonyms retrieved from ChromaDB metadata are preserved through candidate construction and available to synonym-aware matching logic, so that exact synonym matches (for example `CLL`) resolve deterministically.

## Non-goals

* Do not change ChromaDB schema or rebuild the index.
* Do not change matching rules introduced in Ticket #20.
* Do not expand audit alternates to include full synonym lists.
* Do not modify decision routing or repair logic.

---

## Tasks

### 1) Preserve synonyms in candidate objects

Locate the code that converts ChromaDB query results (`metadatas`) into internal candidate representations. Likely locations:

* `src/rag/candidate.py`
* `src/rag/retrieve.py`
* or equivalent helper used by `ontology_match.py`

Actions:

* Ensure each candidate carries:

  * `label`
  * `term_id`
  * `source`
  * **`synonyms` (list[str])**
* Populate `synonyms` from `metadata.get("synonyms", [])`.

If a `Candidate` dataclass exists:

* Add a `synonyms: list[str]` field.
* Default to empty list if missing.

If raw metadata dicts are passed instead:

* Ensure `synonyms` is not discarded before matching.

### 2) Ensure synonym matcher reads from preserved synonyms

Verify in `ontology_match.py` that:

* synonym-aware logic checks candidate.synonyms (or equivalent),
* normalization is applied consistently to both raw value and synonyms,
* exact synonym match sets:

  * `status = "MATCHED"`
  * `match_type = "synonym_exact"`
  * `matched_via = "synonym"`
  * `matched_synonym = <exact synonym string>`
  * `score = 1.0`

No fallback or confidence thresholds should override this.

### 3) Keep audit alternates compact

Alternates in audit output may remain unchanged (no synonym lists needed).
Only the primary match needs to record `matched_synonym`.

### 4) Add regression test for synonym propagation

Add or extend tests to cover the real failure mode:

* Construct a candidate object the same way retrieval does, with:

  * label = `"chronic lymphocytic leukemia"`
  * synonyms include `"CLL"`
* Raw value = `"CLL"`
* Expected:

  * synonym_exact match
  * matched_term_id = DOID:1040
  * score = 1.0

This test must fail without synonym propagation and pass after the fix.

---

## Acceptance criteria

* `uv run pytest -q` passes.
* Disease value `"CLL"` resolves to DOID:1040 via `synonym_exact`.
* Audit output includes:

  * `matched_via: "synonym"`
  * `matched_synonym: "CLL"`
* No changes to unrelated ontology matching behavior.

---

## Ticket file requirement (MANDATORY)

After writing this ticket content, the AI coding agent must create:

```
docs/tickets/ticket-21b.md
```

and copy the full contents of this ticket verbatim into that file.

---
