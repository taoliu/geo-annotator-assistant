# Ticket #127: Curation table UX polish — pinned icon columns, always-on editing, and remove modal

## Background

The AG Grid curation table is now the primary curator workspace. With rich hover tooltips
available, curators can work without a separate details modal.

The first three columns (Status, Checked, Edited) are high-frequency workflow controls
and should be compact, pinned, and self-explanatory.

## Problem Statement

1) The Edited indicator is currently placed at the end of the table and uses text
   (“Yes”/blank), which is space-inefficient and reduces scan speed.
2) Column headers for tiny icon/checkbox columns waste horizontal space.
3) Curators should not be able to reorder the workflow control columns.
4) Usage of the first three columns should be explained inline.
5) “Enable editing” mode switching is unnecessary; editing should always be available.
6) The details modal is now redundant and adds interaction cost; tooltips should
   provide required inspection details.

## Proposed Change

### A) Reorder and compact the first three workflow columns
Reorder columns to:

1. Status (icon)
2. Checked (checkbox)
3. Edited (icon)
4. gse_accession
5. gsm_accession
6. ... remaining fields ...

### B) Edited column as pencil icon (no text)
- The Edited column must no longer display “Yes” or empty string.
- If the row has been edited (session or saved overrides, as currently defined in UI):
  - display a pencil-style icon in the Edited column.
- If not edited:
  - display nothing.

### C) Remove header text for Checked and Edited (and Status if not already)
- Do not display header text for:
  - Status
  - Checked
  - Edited
- Keep the columns functional and visible, but with blank headers.
- Ensure these three columns use minimal width.

### D) Pin and lock the first three columns
The first three columns (Status, Checked, Edited) must:

- be pinned to the left (remain visible during horizontal scroll)
- be non-movable / locked in position
- be non-resizable (optional, if needed to keep widths stable)

### E) Add explanation text above the table
Add a short help line above the curation table explaining the first three columns.
Example content (exact wording may vary, keep concise):

- Status: click icon to open details (NOTE: see section F for modal removal)
- Checked: curator review marker, saved to disk
- Edited: pencil indicates this row has curator edits/overrides

Because the modal is being removed (F), update the Status explanation to match the new behavior:
- Status: indicates row state (flagged/clean); details are available via hover tooltips.

### F) Always-on editing (remove edit mode toggle)
- Remove the “Enable editing” toggle / mode selection from the UI.
- Editing is always enabled (the only curator mode).

### G) Remove detail modal behavior
- Remove the feature that opens a modal dialog for GSM details.
- Clicking the Status icon must no longer open a modal.
- Curator inspection is done via hover tooltips in-table.
- Keep the existing tooltip content and ensure it contains all necessary
  diagnostics (per Ticket #125).

(If any information was previously only available in the modal, it must be surfaced
via tooltips or inline UI text, but without triggering backend computation.)

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change (policy-spec.md must be updated)

## Acceptance Criteria

- Column order is Status, Checked, Edited, then gse_accession, gsm_accession, etc.
- Edited column displays a pencil icon only when the row is edited, with no “Yes” text.
- Status/Checked/Edited columns have no header text and are narrow.
- Status/Checked/Edited columns are pinned left and cannot be moved.
- A concise explanation text block appears above the table describing these columns.
- Editing is always enabled; there is no edit mode toggle.
- No modal opens anywhere from the table; detail inspection is via hover tooltips.
- No backend artifacts are modified by these UX changes (checked persistence remains UI-only).

## Non-Goals

- Do not introduce new inference or recomputation.
- Do not change override semantics.
- Do not change backend decision routing or outputs.

## Constraints

- UI-only change.
- Keep deterministic column definitions and stable ordering.

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-127.md` and paste this ticket verbatim.
