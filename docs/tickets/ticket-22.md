# Ticket #22: AGENT-WS-022 — Exact label fallback for ontology grounding when vector recall fails

You are working in repo `geo-gsm-annotator-agent`.

## Context

We observed that some ontology terms exist in Chroma (retrievable via `collection.get(where=...)`) but are never returned by vector search, even when querying with the term’s own document embedding. Example:

* `EFO:0007045` label `ATAC-seq` exists and has a valid document text.
* Vector query top50 for “ATAC-seq” does not include it.
* Querying with embedding(document of EFO:0007045) still does not retrieve itself.

This causes `data_type="ATAC-seq"` to be grounded as LOW_CONFIDENCE despite the correct term existing.

## Goal

Add a deterministic fallback path: when grounding a field value, attempt an exact metadata lookup by label and inject exact hits into candidate list before scoring. This ensures `label_exact` can match even if vector recall misses the correct term.

## Scope

* Implement in the ontology retrieval layer (likely `src/rag/ontology_retrieve.py`).
* No DB rebuild. No changes to Chroma files.
* Keep existing vector retrieval behavior; add an additional exact lookup.

## Tasks

1. Add a small canonicalization helper for label lookup:

   * normalize whitespace/hyphen variants for common assay strings
   * at minimum: map “ATAC seq” / “ATACseq” / “atac seq” → “ATAC-seq”

2. In `retrieve_ontology_candidates(...)`:

   * after vector `collection.query(...)`, call:

     * `collection.get(where={"source": source, "label": canonical_label}, include=["metadatas","documents"])`
   * Convert results to `OntologyCandidate`s.
   * Prepend them to the candidates list if not already present by `term_id`.

3. Ensure synonyms coercion remains robust (string/list supported).

4. Add unit test:

   * Mock/stub Chroma collection so vector query does NOT return `EFO:0007045`,
   * but `get(where={source,label})` DOES return it,
   * verify `choose_best_ontology_candidate("ATAC-seq", ...)` yields MATCHED label_exact term_id `EFO:0007045`.

5. Run: `uv run pytest -q`

## Acceptance criteria

* For raw_value `ATAC-seq` with ontology `Experimental Factor Ontology`, grounding returns:

  * `status: MATCHED`
  * `match_type: label_exact`
  * `matched_term_id: EFO:0007045`
  * `confidence: 1.0`
* Tests pass.

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-22.md` and paste this ticket verbatim.

---
