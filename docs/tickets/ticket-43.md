# Ticket #43: UI-005 — Inline editing in curation table (data_editor) + derive in-memory overrides

## Background

Ticket #42 introduced edit mode with in-memory overrides. Curators would prefer editing directly in the table. Streamlit supports inline editing via `st.data_editor`. This ticket upgrades the editing UX while keeping safety invariants:

* Edit is disabled by default
* No persistence beyond session memory
* No file writes (export is a later ticket)
* Only canonical fields are editable

---

## Scope (STRICT)

**In scope**

1. In edit mode, replace the main table with an inline-editable table:

   * Use `st.data_editor`
   * Show one row per GSM
2. Restrict editable columns to canonical fields only:

   * Editable: `data_type`, `organism`, `tissue_type`, `cell_line`, `disease`, `treatment`
   * Read-only: `gse_accession`, `gsm_accession`, and any derived columns (flags, edited marker)
3. On table edits:

   * Compute diffs against the original loaded `curation.jsonl`
   * Update the in-memory overrides map exactly as in Ticket #42:
     `(gse_accession, gsm_accession, field) -> value`
4. Add controls:

   * “Revert selected row” (clears overrides for that GSM and restores displayed values)
   * “Clear all edits”
5. Keep highlighting from Ticket #41:

   * flagged cells still highlighted (at minimum in read-only mode)
   * if full cell styling is hard in `data_editor`, then in edit mode show flags in a separate compact column (for example: `flagged_fields="disease,tissue_type"`)

**Out of scope**

* Exporting `overrides.jsonl`
* Any validation beyond allowed fields and basic JSON-serializable values
* Any backend pipeline changes

---

## UX requirements

* Edit mode toggle remains explicit and defaults to OFF.
* Inline edits must feel safe:

  * show a persistent “Unsaved edits (session-only)” indicator when overrides exist
  * show count: `Edited GSMs: N`, `Edited fields: M`
* If a user edits and then disables edit mode:

  * edits remain in memory and still show “edited” markers
  * but table returns to read-only display (no loss unless user explicitly clears)

---

## Implementation notes

1. Maintain two DataFrames:

   * `df_base`: from `curation.jsonl` (normalized)
   * `df_view`: `df_base` plus derived columns (flags, edited marker)
2. In edit mode:

   * feed `df_editable` to `st.data_editor` containing only id columns + canonical fields
   * compare returned edited df with `df_base` to compute diffs
3. Diff logic must be deterministic and pure for tests:

   * `compute_overrides(df_base, df_edited) -> overrides_map`
   * Must ignore non-canonical columns and ignore no-op edits (same value)
4. Styling:

   * If `data_editor` cannot reliably do per-cell background colors, do not force it.
   * Use a `flagged_fields` string column or a right-side panel for flags while editing.

---

## Acceptance Criteria

* Curator can edit canonical fields directly in the table when edit mode is ON.
* Only canonical fields are editable; accession columns are not editable.
* Overrides map updates correctly and deterministically from table edits.
* “Revert row” and “Clear all edits” work.
* No file writes occur.
* Read-only mode remains the default and stable.

---

## Tests Required

1. Unit tests for `compute_overrides(df_base, df_edited)`:

   * single-cell edit produces one override
   * multiple edits in one row produce multiple overrides
   * editing back to original removes the override
   * order independence (edit sequence does not matter)
2. Unit test that non-canonical columns are ignored in diff.

---

## Non-Goals (Explicit)

* No export in this ticket.
* No suggestion auto-apply.
* No persistence beyond session memory.

---

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-43.md` and paste this ticket verbatim.
