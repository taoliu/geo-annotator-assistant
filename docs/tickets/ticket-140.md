# Ticket #140: Bulk edit single column across selected GSMs (explicit, reversible, UI-only)

## Background

Curators often need to apply the same correction to many GSMs within a GSE
(e.g., same `data_type`, `tissue_type`, or `disease`). Doing this cell-by-cell is slow.

We want a bulk edit feature that is:
- explicit
- reversible
- audit-friendly
- does not introduce inference or cross-GSM propagation logic

## Problem Statement

The current table supports per-cell editing only. For large GSEs, repeated edits to the
same column across many rows are time-consuming and error-prone.

## Proposed Change

Add an explicit bulk edit workflow for applying a single value to a single column
across multiple selected rows.

### A) Selection model (AG Grid)
Enable multi-row selection in the curation table.

- Curator selects multiple rows (GSMs) to target.
- Bulk edit applies to the selected rows only.
- No implicit “select all filtered” behavior unless explicitly added later.

### B) Bulk edit panel (above table)
Add a compact “Bulk edit” panel above the curation table containing:

1) **Target column** dropdown (only editable output fields):
   - `data_type`, `organism`, `tissue_type`, `cell_line`, `disease`, `treatment`
   (Do not include `gse_accession` or `gsm_accession`.)

2) **New value** input:
   - plain text box
   - optional “Use value from focused cell” quick-fill if feasible

3) **Apply to selected (N)** button:
   - disabled if no rows selected
   - disabled if column not chosen or value empty (unless empty is a valid value per field rules)

4) **Preview summary** (must be shown before apply):
   - Selected row count (N)
   - Column name
   - New value
   - Count of rows where this would be a no-op (already equal)
   - Count of rows that would change

Implementation detail:
- The preview may update live as inputs change, but the actual write happens only on Apply.

### C) Safety checks (must reuse existing UI safety rules)
Before applying:
- Run the same per-cell override safety validation currently used by single-cell edits
  (e.g., any `override_safety` checks).
- If some rows fail validation, do not partially apply silently.

Required behavior:
- Either:
  - block apply and show a small table/list of the GSMs that would be rejected and why, OR
  - allow “Apply only to valid rows” as an explicit second button (optional).
For v1.1, default to “block and explain” to avoid accidental partial operations.

### D) Edit semantics and reversibility
Bulk edit produces normal UI edits (session edits) exactly as if the curator edited each
cell manually, meaning:

- Edited pencil indicator updates immediately for affected rows.
- “Revert selected row” reverts a row’s bulk edits like any other edits.
- “Clear all edits” clears bulk edits like any other edits.
- “Save overrides” persists the resulting changes as overrides, identical to manual edits.

No new persistence format is introduced by bulk edit.

### E) Scope constraints (explicit)
- Bulk edit applies only within the currently selected GSE table.
- No cross-GSE bulk apply.
- No inference, no ontology re-grounding, no auto-fill across rows.

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change (policy-spec.md must be updated)

## Acceptance Criteria

- Curator can multi-select rows and apply a single value to a single chosen column.
- A preview is shown before apply, including (N selected, N changed, N no-op).
- The apply operation updates the table immediately (no Ctrl+R required).
- Edited indicators update immediately for affected rows.
- Revert and clear edits work correctly for bulk-applied changes.
- Override safety validation is enforced; failures are surfaced to the curator.
- No backend processes are triggered, and no backend artifacts are modified.

## Non-Goals

- No bulk editing across multiple columns in one action.
- No “smart fill” or pattern-based propagation.
- No ontology-based normalization or validation added in the UI.
- No automatic selection of rows based on flags unless separately ticketed.

## Constraints

- UI-only change.
- Operation must be explicit and reversible.
- Prefer deterministic behavior over convenience.

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-140.md` and paste this ticket verbatim.
