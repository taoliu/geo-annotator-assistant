# Ticket #49: RAG-ONTO-007 — Deterministic “exact-first” retrieval path for ontology lookup (fix Chroma ANN miss)

## Background

We observed a correctness bug in ontology retrieval: canonical terms like `Myc-CaP` exist in Chroma (Cellosaurus source) and are retrievable by ID/metadata/document text, but **ANN vector search (HNSW)** sometimes fails to return them in large, clustered collections. The correct fix is to **not rely on vector search alone** for ontology/entity lookup.

We will implement a deterministic retrieval strategy in `src/rag/ontology_retrieve.py`:

1. exact ID lookup (when applicable)
2. exact label match
3. deterministic substring/contains match against documents
4. only then fall back to vector similarity search

This preserves the project invariants: retrieval remains deterministic, read-only, auditable, and supplies candidates only.  

---

## Scope (STRICT)

### In scope

1. **Add an exact-first retrieval path** inside `src/rag/ontology_retrieve.py` for ontology candidate lookup (Cellosaurus and any other ontology sources using Chroma):

   **Ordered strategy (MANDATORY):**

   1. **Exact ID lookup** (when the query looks like a canonical ID pattern for the source, or when metadata includes ID fields):

      * Use `collection.get(ids=[...])` when we can map query → Chroma ID deterministically.
      * If the project stores ontology IDs in metadata, allow `where={"id": ...}` (or source-specific metadata key) as a secondary exact path.

   2. **Exact label match**:

      * Use a deterministic query against stored label field if present in metadata (for example `where={"label": query}`).
      * If labels are only in `documents`, do a document-equality match if supported; otherwise skip to contains.

   3. **Deterministic substring match against document text**:

      * Use Chroma `where_document={"$contains": ...}` with a normalized query string.
      * Must include a normalization that preserves punctuation like `-` (do not drop hyphens for cell line names).
      * If multiple matches, return top-K deterministically using a stable sort (see below).

   4. **Vector similarity fallback**:

      * Keep existing ANN search as a fallback only.
      * If config already provides `hnsw:search_ef` tuning, do not change defaults in this ticket.

2. **Deterministic ranking for non-vector matches**

   * For exact/contains matches producing multiple candidates:

     * stable sort by:

       1. exact label equality first (if label available)
       2. shorter document length first (proxy for canonical record)
       3. lexicographic by `id` (or by Chroma internal id) as final tie-break
   * Return top-K with deterministic order.

3. **Auditable retrieval path**

   * Add a small structured field in the returned candidate object (or existing audit channel) indicating:

     * `retrieval_mode`: `id_exact` | `label_exact` | `doc_contains` | `vector_fallback`
     * `query_norm`: the normalized query used for contains/vector
   * No free-text rationale.

4. **Preserve retrieval config governance**

   * Any config changes must remain under `rag.*` / `rag.ontology.*`. 
   * Prefer no config changes unless required.

### Out of scope

* Re-ingesting ontology data
* Changing ontology grounding thresholds or decision routing
* Adding new retrieval backends
* Changing vector index parameters (like HNSW efConstruction/M) or re-building Chroma
* “Fuzzy matching” beyond deterministic contains and existing vector fallback

---

## Acceptance Criteria

1. Given a Chroma collection that contains a document or label with `Myc-CaP`, querying `Myc-CaP` returns it via `label_exact` or `doc_contains` even if vector search would miss it.
2. Retrieval remains deterministic across runs:

   * same query → same ordered candidates
3. Existing tests pass.
4. Add new tests proving the exact-first path works and that vector fallback is still used when exact/contains fail.

---

## Tests Required

Add `tests/test_ontology_retrieve_exact_first.py` (or extend existing ontology retrieval tests) covering:

1. **Contains match success**

   * Build or mock a small Chroma collection with documents including `Myc-CaP`
   * Force vector fallback to return unrelated hits (or disable vector call in the mock)
   * Assert retrieval returns `Myc-CaP` via `doc_contains`

2. **Exact label match success**

   * If labels are stored in metadata, assert `label_exact` mode triggers and returns the correct entry.

3. **Deterministic ordering**

   * Insert multiple docs containing the query
   * Assert candidate order is stable and follows the tie-break rules.

4. **Vector fallback preserved**

   * Query a string not present in any document/label
   * Assert retrieval_mode is `vector_fallback` and results come from ANN path.

---

## Implementation notes

* Prefer implementing this logic in a single helper function inside `ontology_retrieve.py`, for example:

  * `_retrieve_exact_first(collection, query, k, source_config) -> list[Candidate]`

* Normalization guidance:

  * trim whitespace
  * preserve hyphen and case-sensitive tokens for cell line names
  * also try a secondary normalized form (case-folded) for contains match, but keep the original first.

* If Chroma `where_document` contains match is slow at scale, keep K small and rely on deterministic early exit. This ticket focuses on correctness, not performance tuning.

---

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-49.md` and paste this ticket verbatim.

---
