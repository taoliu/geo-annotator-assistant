# Ticket #53: RAG-ONTO-011 — Short-circuit embeddings and vector fallback on terminal exact hits

## Background

Even when ontology grounding reports an exact match (for example `match_type="synonym_exact"` with `score=1.0`), the current pipeline can still trigger embedding-based vector queries for that field. This is unnecessary work and can be a major speed bottleneck in large ontology collections.

We will introduce a single explicit predicate in code:

```python
is_terminal_exact = (
    status == "MATCHED"
    and score == 1.0
    and match_type in {"label_exact", "label_norm_exact", "synonym_exact", "term_id_exact"}
)
```

If `is_terminal_exact` is true for a field, we must **stop** any embedding calls and **skip** any vector fallback for that field.

This change is performance-focused and must not alter match outcomes (it only avoids work after an exact result is already known).  

---

## Scope (STRICT)

### In scope

1. **Define and use `is_terminal_exact` predicate**

   * Implement the predicate in a shared location (preferred) or in the ontology grounding module, and reuse it consistently.
   * Predicate must be exactly:

   ```python
   TERMINAL_EXACT_TYPES = {"label_exact", "label_norm_exact", "synonym_exact", "term_id_exact"}

   def is_terminal_exact(status: str, score: float, match_type: str) -> bool:
       return status == "MATCHED" and score == 1.0 and match_type in TERMINAL_EXACT_TYPES
   ```

2. **Short-circuit behavior**
   When `is_terminal_exact(...)` is true for a field’s selected match:

   * Do not call `collection.query(...)` (vector search) for that field.
   * Do not compute embeddings for that field (no `query_texts` embedding step).
   * Do not run any “populate alternates via vector search” logic for that field.

3. **Deterministic alternates policy on terminal exact**

   * On terminal exact, alternates must be deterministic and must not require embeddings.
   * Allowed options (choose one, but make it explicit and tested):

     * Option A (preferred): `alternates = [matched_term_only]`
     * Option B: keep existing alternates generation only if it is already deterministic and embedding-free

4. **Audit visibility**

   * Ensure the match record (in audit) clearly indicates that short-circuit happened, via one of:

     * `retrieval_mode` stays as `meta_exact` / `id_get` and no `vector_fallback` entry exists, OR
     * add a small boolean field: `vector_fallback_skipped: true` (diagnostics-only)

### Out of scope

* Any canonicalization of output labels (that is Ticket #54)
* Any change to thresholds or match selection logic
* Any token splitting or fuzzy string matching beyond what already exists
* Any change to repair loop semantics

---

## Acceptance Criteria

1. If a field match is terminal exact (MATCHED, score 1.0, match_type in the set), then:

   * No vector fallback is executed for that field.
   * No embedding calls occur for that field.
2. Match outcome (matched term_id/label/status/match_type/score) is unchanged compared to before, aside from any alternates list differences allowed by the deterministic policy chosen.
3. Existing tests pass.
4. New tests confirm the short-circuit behavior reliably triggers for `synonym_exact` score 1.0.

---

## Tests Required

Add `tests/test_terminal_exact_short_circuit.py`:

1. **No vector query on terminal exact**

   * Mock `collection.query` and assert it is not called when the selected match satisfies `is_terminal_exact`.

2. **No embedding calls on terminal exact**

   * Mock / wrap the embedding function used by Chroma (or mock the place where embeddings are invoked) and assert zero calls.

3. **Positive coverage for synonym_exact**

   * Provide a match object with:

     * `status="MATCHED"`, `score=1.0`, `match_type="synonym_exact"`
   * Assert short-circuit triggers.

4. **Negative coverage**

   * For `LOW_CONFIDENCE` or `MATCHED` with `score < 1.0`, assert vector fallback can still occur.

---

## Implementation notes

* The short-circuit should happen at the earliest point where the code has the chosen match triple `(status, score, match_type)` for that field.
* Keep the predicate definition close to matching logic so future edits do not diverge.
* If your current code always calls vector query to fill alternates, refactor so alternates can be optional and embedding-free for terminal exact.

---

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-53.md` and paste this ticket verbatim.
