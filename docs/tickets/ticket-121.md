# Ticket #121: AG Grid regression fixes — restore flagged cell highlighting and enable status-cell click to open modal

## Background

The curation table was migrated to AG Grid to support rich hover tooltips and direct
status-cell interactions. After the initial integration:

1) Field-level flagged cell background highlighting is no longer shown.
2) Clicking status icons (flag/check) does not open the GSM details modal.

## Problem Statement

The table lost two core curator affordances from v1.0:
- visual scanning via flagged-cell coloring
- intuitive modal opening via the status icon

This is a UI regression caused by missing AG Grid event + styling wiring.

## Proposed Change

### A) Restore flagged cell background highlighting
- Implement AG Grid cell-level styling for biology fields using `cellClassRules`
  (or an equivalent deterministic mechanism).
- Rules must be based on existing row metadata already loaded by the UI
  (e.g., `flagged_fields`, field-level flags, or equivalent).
- Apply the same “flagged” background color used in the v1.0 Streamlit table.

### B) Enable status icon click to open details modal
- Wire a click handler such that clicking a cell in the `Status` column sets the
  active GSM in `st.session_state` and triggers rendering of the existing details modal.
- Ensure this works even when row selection is suppressed or custom renderers are used.
- Do not require checkbox selection.

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change (policy-spec.md must be updated)

## Acceptance Criteria

- For a GSM row with a flagged field, the corresponding cell background is highlighted
  consistently with the previous UI.
- Clicking the flag/check cell in the `Status` column reliably opens the GSM details modal.
- No backend execution is triggered by these interactions.
- Existing tooltip behavior remains unchanged.

## Non-Goals

- No changes to backend flags, decisions, or audit formats.
- No new inference logic or recomputation.

## Constraints

- UI-only change.
- Styling and click behaviors must be deterministic and stable across reruns.

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-121.md` and paste this ticket verbatim.
