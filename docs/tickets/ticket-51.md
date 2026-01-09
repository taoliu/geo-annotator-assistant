# Ticket #51: RAG-ONTO-009 — Fix exact-match scoring/type for normalized metadata matches (Cellosaurus Myccap → Myc-CaP)

## Background

In `audit.jsonl`, the `cell_line` field shows:

* `alternates` contains the correct term (`CVCL:J703`, `Myc-CaP`)
* but `status=LOW_CONFIDENCE`, `match_type=jaccard`, `score=0.0`

This indicates the retrieval path found the correct term deterministically, but the **match classifier/scoring** did not recognize it as an **exact normalized metadata match**. With the new schema, if `label_norm` (or source-specific field variants) matches, it must be reported as exact with score/confidence 1.0.

---

## Scope (STRICT)

### In scope

1. In `src/rag/ontology_retrieve.py` (and/or the grounding/matching module that assigns `match_type/score/status`), ensure that when the deterministic metadata query hits via:

   * `label_norm` / `label_norm_compact` / `label_norm_space`, or
   * the source-specific normalized fields (`cell_line*`, etc.)

   then the match record is set as:

   * `status: "MATCHED"`
   * `match_type: "label_norm_exact"` (or `"label_exact"` if you prefer not to introduce a new enum; but must be unambiguous)
   * `score: 1.0`
   * `alternates[0].confidence: 1.0`
   * `matched_term_id/label/source` populated

2. Ensure that the “exact match” determination is driven by the deterministic path that already computed the `hyphen/compact/space` variants:

   * For example, if candidate normalization produced `myc-cap` and the retrieved metadata field equals that variant, it is exact.

3. Keep vector fallback scoring unchanged.

### Out of scope

* Changes to repair loop logic
* Changes to decision routing / flag thresholds
* Any change that would introduce fuzzy token splitting

---

## Acceptance Criteria

1. For a query like `Myccap` (or `Myc-CaP`) mapping to `CVCL:J703 / Myc-CaP` through normalized metadata, the audit record shows:

   * `status=MATCHED`, `score=1.0`, and an exact match type.
2. Existing tests pass.
3. Add a unit test that reproduces the bug and validates the corrected match output fields.

---

## Tests Required

Add `tests/test_ontology_match_scoring_exact_norm.py`:

* Build a small mock Chroma collection metadata containing a Cellosaurus record with:

  * `label_norm = "myc-cap"`, `label_norm_compact="myccap"`, `label_norm_space="myc cap"`
  * plus the `cell_line*` equivalents if used
* Query with raw value `"Myccap"`
* Assert:

  * `MATCHED`, `score=1.0`, `match_type` exact
  * returned `term_id="CVCL:J703"` and `label="Myc-CaP"`

---

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-51.md` and paste this ticket verbatim.

---
