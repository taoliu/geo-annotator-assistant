# Ticket #122: Extend AG Grid flagged-cell highlighting to essential biology columns

## Background

After migrating the curation table to AG Grid, cell background highlighting for flagged
content was partially restored. Some diagnostic columns now show color, but the five
essential biology columns do not consistently highlight flagged fields.

Curators rely on these highlights to scan large GSEs quickly.

## Problem Statement

The AG Grid table does not highlight flagged cells for:
- data_type
- organism
- tissue_type
- cell_line
- disease

As a result, the table is less scannable and important review signals are muted.

## Proposed Change

Extend AG Grid cell-level styling to apply the existing “flagged” highlight color to
cells in the five essential biology columns whenever that field is flagged for the row.

Implementation requirements:

- Use deterministic AG Grid styling (`cellClassRules` preferred).
- Drive rules using existing row metadata already loaded by the UI
  (e.g., `flagged_fields`, per-field flags, or equivalent).
- Apply the same highlight color semantics as the v1.0 UI.
- Keep the diagnostic column coloring unchanged.

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change (policy-spec.md must be updated)

## Acceptance Criteria

- For any row where `flagged_fields` includes one of:
  `data_type`, `organism`, `tissue_type`, `cell_line`, `disease`,
  the corresponding cell in that column is highlighted.
- Highlighting is stable across reruns and does not depend on tooltip hover.
- No backend execution is triggered.
- No new inference or aggregation is introduced.

## Non-Goals

- Do not introduce new flags or reinterpret existing ones.
- Do not color cells based on “similarity score” or any heuristic not already present.

## Constraints

- UI-only change.
- Styling rules must be field-key based, not string matching on text.

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-122.md` and paste this ticket verbatim.
