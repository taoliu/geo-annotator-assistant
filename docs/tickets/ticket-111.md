# Ticket #111: Curation Table Column Reordering and Decision Icon Row Affordance

## Background

The curation table is the primary navigation surface. After v0.9, the table has
grown with triage and policy columns. Curators, however, most often need to scan
the core 6 biology fields immediately after identifying the GSM.

The current table layout also uses a checkbox column that is not essential for
navigation, and the Decision column occupies prominent space that can be
represented more compactly.

## Problem Statement

1) The essential 6 fields (`data_type`, `organism`, `tissue_type`, `cell_line`,
   `disease`, `treatment`) are not placed early in the row, forcing horizontal
   scanning.

2) Row navigation uses a checkbox column and a separate click target, while the
   decision state is shown as text.

3) The “Needs attention” column is redundant with decision state (FLAGGED vs
   ACCEPT) and increases visual noise.

## Proposed Change (UI Only)

### 1) Reorder Columns (Essential Fields First)

In the curation table, reorder columns so that the row begins with:

- Status icon (see below)
- `gse_accession`
- `gsm_accession`
- `data_type`
- `organism`
- `tissue_type`
- `cell_line`
- `disease`
- `treatment`

All other columns (primary failure, flag summary, outliers, review flags,
terminal fallbacks, edited/overrides indicators, etc.) should be placed after
these core fields (or remain available via optional column toggles if the UI
already supports that concept).

No underlying data changes, only display order.

### 2) Replace Checkbox Column with Decision Icon and Click-to-Open

Replace the first column (checkbox) with a single status icon that acts as the
row’s primary click target:

- `✅` for `final_decision == ACCEPT`
- `🚩` for `final_decision == FLAGGED`

Behavior:
- Clicking the icon opens the GSM modal (same behavior as current row open).
- The icon must include a tooltip with the decision label (“ACCEPT” / “FLAGGED”).
- This change removes the need for a checkbox selection column.

Consequences:
- Remove the separate “Decision” column entirely (redundant).
- Ensure keyboard accessibility is preserved as best as possible within the
  current Streamlit/table constraints (at minimum: icon is clickable and has a
  tooltip).

### 3) Remove “Needs attention” Column

Remove the “Needs attention” column from the curation table.

Rationale:
- It is redundant with `final_decision` and the new decision icon.
- Curator attention is already guided by FLAGGED and by flags/primary failure.

### Inputs and Guardrails

- Use `curation.jsonl.final_decision` as the source of truth for the icon.
- No inference, no change to backend semantics.
- Do not remove data from the modal; only adjust table layout.

## Why No Backend Change Is Required

All changes are purely presentational and driven by existing fields in
`curation.jsonl`.

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change

## Acceptance Criteria

1. The curation table shows the 6 essential fields immediately after GSE/GSM.
2. The first column is a decision icon (`✅` / `🚩`) and is clickable to open the modal.
3. The “Decision” column is removed.
4. The “Needs attention” column is removed.
5. Existing filtering and sorting still function (even if they operate on hidden
   columns internally).
6. No JSONL files are modified.

## Non-Goals

- No changes to the GSM modal content beyond how it is opened.
- No new decision categories beyond ACCEPT/FLAGGED.
- No backend changes.

## Constraints

- Maintain table performance for large GSEs.
- Preserve determinism and auditability.
- Keep the UI read-only except where overrides are explicitly saved/exported
  (Ticket #110).

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-111.md` and paste this ticket verbatim.
