# Ticket #23: AGENT-WS-023 — Detect cell types vs cell lines and apply deterministic fallback

### Background

Many GEO samples use **primary cells or cell types** (e.g. *CD8+ T cells, PBMC, hepatocytes*) rather than immortalized cell lines. These values should **not** be grounded against **Cellosaurus**, and the current behavior produces systematic `ontology_low_confidence_cell_line` false positives.

Example:

```
cell_line = "CD8+ T cells"
```

This is a cell type, not a cell line. Correct behavior is to mark **no cell line used**.

### Problem

* Cellosaurus grounding is attempted for values that are biologically cell types.
* This causes unnecessary LOW_CONFIDENCE flags and repair attempts.
* This is a semantic type error, not an ontology coverage issue.

### Goal

Introduce a **cell-line type guard** that detects when `cell_line` values represent cell types and deterministically falls back to `"No"` (or `"Unknown"` if configured), without invoking ontology matching.

### Scope

* `cell_line` field only
* Deterministic logic, no LLM required for the primary path

### Requirements

#### 1. Add a new semantic failure code

Add a new failure code:

```
cell_line_is_cell_type
```

#### 2. Detection heuristic (simple, rule-based)

Before ontology grounding for `cell_line`, detect cell-type patterns. Trigger `cell_line_is_cell_type` if **any** of the following hold (case-insensitive):

* Value contains or ends with `"cells"` or `"cell"`
* Contains immune markers: `CD3`, `CD4`, `CD8`, `B cell`, `T cell`, `NK`
* Contains `PBMC`, `splenocyte`, `thymocyte`
* Contains `primary`, `sorted`, `fresh`, `ex vivo`
* Contains `"+"` **and** `"cell"` (e.g. `CD8+ T cells`)

This list should be implemented as a small utility function.

#### 3. Decision table update

Add rule to `decision_table.yaml`:

```
cell_line_is_cell_type:
  action: FALLBACK
  field: cell_line
  repair_template: null
  max_attempts: 0
  fallback_value: "No"
  severity: low
```

(Use `"Unknown"` instead of `"No"` only if project policy requires.)

#### 4. Ontology behavior

* If `cell_line_is_cell_type` is triggered:

  * Skip Cellosaurus grounding entirely
  * Record ontology status as `FALLBACK`
  * Do **not** raise `ontology_low_confidence_cell_line`

#### 5. Audit output

Ensure audit records:

* failure_code: `cell_line_is_cell_type`
* fallback applied with value `"No"`
* no ontology alternates listed

#### 6. Tests

Add unit tests covering:

* `"CD8+ T cells"` → `cell_line="No"`, ACCEPT
* `"PBMC"` → `cell_line="No"`
* `"HepG2"` → still grounded via Cellosaurus
* `"Jurkat"` → still grounded via Cellosaurus

### Acceptance criteria

* No LOW_CONFIDENCE or AMBIGUOUS flags for cell-type values in `cell_line`
* GEO samples with primary cells pass without escalation
* Behavior is deterministic and documented

### Documentation

* Briefly note this rule in `whitepaper.md` (validation semantics section)
* Mention in milestone v0.3 goals if applicable

---
