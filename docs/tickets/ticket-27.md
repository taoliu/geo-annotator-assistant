# Ticket #27: AGENT-WS-027 — Enforce anatomy-only constraint for `tissue_type` (prevent cell-type leakage)

## Background

Real-world GEO datasets frequently describe **cell types** (for example, “primary mouse mammary fibroblasts”) in fields that the LLM may incorrectly map to `tissue_type`. However, by design, `tissue_type` in this pipeline is intended to represent **anatomical structures** (Uberon-level), not cell types or cell states.

In GSE229352, several GSMs were flagged because:

* The LLM populated `tissue_type` with a cell type (“Primary mouse mammary fibroblasts”).
* Uberon grounding correctly returned LOW_CONFIDENCE.
* The repair loop repeatedly attempted ontology-guided repair without correcting the category.
* The run exhausted repair budget and ended in `max_repairs_exceeded`.

This mirrors an already-solved problem for `cell_line` (cell type vs cell line), but no equivalent constraint exists for `tissue_type`.

## Goal

Introduce an explicit semantic constraint that **`tissue_type` must be an anatomical term**, not a cell type, and handle violations deterministically to avoid wasted repair attempts.

## Non-goals

* No ontology redesign
* No prompt redesign
* No changes to disease or cell_line semantics beyond existing rules
* No changes to downstream consumers or output schema

## Policy to implement

### New semantic failure

Introduce a new semantic failure code:

* `tissue_type_is_cell_type`

Trigger condition (heuristic, conservative):

* `tissue_type` contains known cell-type indicators such as:

  * `fibroblast(s)`
  * `cell`, `cells`
  * `macrophage`
  * `epithelial`
  * `lymphocyte`, `T cell`, `B cell`, etc.
* Or matches existing cell-type detection logic already used for `cell_line`, where applicable.

### Repair behavior

Decision routing for `tissue_type_is_cell_type`:

1. **Repair attempt (evidence-first)**

   * Use context evidence to propose an **anatomical structure** (Uberon-level).
   * Example:

     * If context contains “mammary” or “breast”, propose `Breast` / `mammary gland`.
   * Use existing repair prompt (`repair_ontology_guided_v1`) or a small variant if needed, with explicit instruction:

     * “Return an anatomical tissue term, not a cell type.”

2. **Fallback**

   * If repair fails after configured attempts, fallback:

     * `tissue_type = "Unknown"`

3. **Stop condition**

   * Once `tissue_type` is fallbacked to a terminal value, do not re-attempt repairs for this field in the same run.

## Implementation plan

### 1. Semantic validator

* Extend `validator/semantic_validator.py` (or appropriate module) to detect `tissue_type_is_cell_type`.
* Reuse or mirror logic from existing `cell_line` vs cell-type guards where possible.

### 2. Failure mapping

* Add `tissue_type_is_cell_type` to failure code definitions and decision table routing.
* Ensure it maps to the repair behavior described above.

### 3. Repair loop safeguards

* Ensure this new failure does not endlessly re-trigger after fallback.
* One repair attempt + fallback should be sufficient in most cases.

### 4. Tests

Add unit tests covering:

1. **Positive case**

   * Context containing “Primary mouse mammary fibroblasts”.
   * LLM output with `tissue_type = "Primary mouse mammary fibroblasts"`.
   * Expect either:

     * repaired `tissue_type = "Breast"` (or equivalent anatomy), or
     * fallback to `Unknown`.
   * Final decision should be `ACCEPT`, not `FLAGGED`.

2. **Negative case**

   * Valid anatomical tissue (for example, “Breast”) should not trigger the new failure.

Tests should run with:

* `llm.mode = stub`
* `rag.ontology.enabled = false`

## Acceptance criteria

* Cell-type strings in `tissue_type` no longer cause `max_repairs_exceeded`.
* GSE229352 no longer produces flagged GSMs solely due to tissue-type misclassification.
* Existing accepted cases remain accepted.
* `uv run pytest -q` passes.

---

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-27.md` and paste this ticket verbatim.
