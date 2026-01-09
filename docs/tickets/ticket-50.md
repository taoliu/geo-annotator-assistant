# Ticket #50: RAG-ONTO-008 — Update Chroma ontology query to new normalized metadata schema (deterministic first, vector fallback)

## Background

Upstream `rag_ontology` build now stores ontology documents in Chroma with:

* `metadatas` containing at least: `source`, `term_id`, `label`
* additional **exact-match-only normalization variants**:

  * `label_norm` (hyphen form)
  * `label_norm_compact` (hyphen removed)
  * `label_norm_space` (hyphen to space)
* plus **source-specific normalized fields** (same 3 variants), keyed by source:

  * `Cellosaurus` → `cell_line`, `cell_line_compact`, `cell_line_space`
  * `Cell Ontology` → `cell_type`, `cell_type_compact`, `cell_type_space`
  * `Uberon Ontology` → `tissue_type`, `tissue_type_compact`, `tissue_type_space`
  * `Human Disease Ontology` → `disease`, `disease_compact`, `disease_space`
  * `Experimental Factor Ontology` → `data_type`, `data_type_compact`, `data_type_space`
  * `NCI Thesaurus` → `cancer_type`, `cancer_type_compact`, `cancer_type_space`

The runtime query logic must be updated to use these metadata fields with a deterministic strategy and only fall back to vector search when deterministic matching fails.

This change must preserve architectural invariants: RAG is deterministic and auditable, read-only, supplies candidates only, and never makes decisions.  

---

## Scope (STRICT)

### In scope

1. **Update Chroma collection access to use a direct embedding function**

   * In `src/rag/chroma_client.py` (or where collection is created), ensure we attach:

     * `chromadb.utils.embedding_functions.SentenceTransformerEmbeddingFunction(model_name="BAAI/bge-base-en-v1.5")`
   * Do **not** pass LangChain embedding classes into Chroma.
   * Ensure `collection.query(query_texts=[...])` works with this embedding function attached.

2. **Rewrite ontology querying strategy in `src/rag/ontology_retrieve.py`**
   Implement the required deterministic-first strategy:

   #### 2.1 Candidate extraction (from user query)

   From the input query string, extract candidate entity strings in this order:

   * quoted spans from `"..."` or `'...'`
   * ID-like tokens matching: `\b[A-Z]{2,10}:[A-Za-z0-9._-]+\b` (example `CVCL:J703`)
   * hyphen/underscore tokens (examples `Myc-CaP`, `NCI-H82`, `myc_cap`)
   * optionally include the whole query if it is short (length < 64 chars after strip)

   Candidate list must be de-duplicated while preserving order.

   #### 2.2 Per-candidate deterministic query logic

   For each candidate:

   **A) ID fast-path**

   * If candidate matches the ID-like regex, try:

     * `collection.get(ids=[candidate])`
   * If found (any document returned), return immediately (top-1 or top-k consistent with current caller contract).

   **B) Exact metadata match with normalization variants**
   Normalize candidate using the same build normalization:

   * lowercase
   * `_` → `-`
   * whitespace → `-`
   * keep only `[a-z0-9-]`
   * collapse multiple `--` to single `-`
   * trim leading/trailing `-`

   Derive three variants:

   * `hyphen` (the normalized form)
   * `compact` (remove `-`)
   * `space` (replace `-` with space)

   Then query with exact metadata match using Chroma `where` with a single top-level operator:

   * If `source` filter is provided, include it via `$and`.
   * Match any of:

     * `label_norm == hyphen`
     * `label_norm_compact == compact`
     * `label_norm_space == space`
   * If `source` is one of the known 6 sources above, also OR the source-specific fields:

     * `{field} == hyphen`
     * `{field}_compact == compact`
     * `{field}_space == space`

   Use Chroma `$and` / `$or` syntax correctly:

   * For multi-clause, Chroma requires a single top-level operator.
   * Example (conceptual):

     * `{"$and": [{"source": "Cellosaurus"}, {"$or": [{"label_norm": hyphen}, ...]}]}`

   **C) Deterministic early return**

   * If deterministic exact match returns >= 1 result, return those candidates immediately (do not continue to other candidates).
   * Deterministic results must be returned with `distance=0.0`.

3. **Vector fallback**
   If no deterministic match is found across all candidates:

   * run vector search:

     * `collection.query(query_texts=[original_query], n_results=k, where={"source": source_filter} if provided)`
   * Return results including `term_id`, `label`, `source`, and distance.

4. **Result schema for callers**
   Ensure returned candidate objects (likely `src/rag/candidate.py`) include at least:

   * `term_id`
   * `label`
   * `source`
   * `distance` (0.0 for deterministic matches; Chroma distances for vector results)
   * `retrieval_mode`: `id_get` | `meta_exact` | `vector_fallback`
   * `query_candidate`: which candidate string triggered the match

5. **No token splitting**

   * Do not split `Myc-CaP` into tokens.
   * Only use whole-label normalization variants (`hyphen`, `compact`, `space`) for exact matching.

### Out of scope

* Rebuilding/ingesting ontology collections
* Changing any validator/decision engine logic
* Changing thresholds or grounding semantics
* Introducing fuzzy token-based string matching (beyond exact metadata match and vector fallback)

---

## Acceptance Criteria

1. With the new metadata schema present, a query for `Myc-CaP` returns the correct Cellosaurus entry via `meta_exact` (or via `id_get` if queried as an ID) even if vector search would miss it.
2. Deterministic-first behavior is enforced:

   * If an exact metadata match exists, vector search is not used.
3. Vector fallback works and returns distances from Chroma.
4. No LangChain embedding class is passed into Chroma; `SentenceTransformerEmbeddingFunction` is used.
5. Existing tests pass, and new tests validate the updated behavior.

---

## Tests Required

Add `tests/test_ontology_chroma_normalized_metadata_query.py` (or update existing ontology Chroma tests) to cover:

1. **Exact metadata match (label_norm variants)**

   * Build a tiny in-memory Chroma collection in the test with metadata fields:

     * `source`, `term_id`, `label`, `label_norm`, `label_norm_compact`, `label_norm_space`
   * Query `Myc-CaP` and assert:

     * retrieval_mode == `meta_exact`
     * distance == 0.0
     * correct `term_id/label/source`

2. **Source-specific fields match**

   * Insert Cellosaurus record with:

     * `cell_line`, `cell_line_compact`, `cell_line_space`
   * Query matches those fields as well.

3. **ID get fast-path**

   * Insert record with ID-like key and ensure `collection.get(ids=[...])` returns it and short-circuits.

4. **Vector fallback**

   * Query a string not present in metadata exact fields and assert vector path used and distance returned.

5. **No token splitting**

   * Ensure the candidate extraction includes `Myc-CaP` as a whole token and does not generate `myc` or `cap`.

---

## Implementation notes

* Candidate extraction should be a pure function for unit testing, e.g.:

  * `extract_candidates(query: str) -> list[str]`
* Normalization should be a pure function:

  * `normalize_exact_variants(s: str) -> dict[str, str]` returning `hyphen/compact/space`
* Use deterministic de-dup preserving order (e.g. seen set).
* Keep config under `rag.*` / `rag.ontology.*` only. 

---

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-50.md` and paste this ticket verbatim.

---
