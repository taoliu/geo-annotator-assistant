# Ticket #130: Fix “Edited” indicator to reflect live session edits and clear correctly on revert

## Background

The curation table includes an “Edited” column (pencil icon) intended to indicate that
a GSM row has curator edits/overrides.

Currently the indicator is inconsistent:
- The pencil icon appears only after saving overrides and hard-refreshing the page.
- The pencil icon does not clear when edits are reverted, unless all edits are discarded.

This suggests the edited-state is being computed from persisted overrides only, and/or
the grid row model is not re-evaluated after edits/reverts.

## Problem Statement

The “Edited” indicator does not reflect curator intent and breaks workflow:
- It should update immediately when a cell is edited.
- It should clear immediately when the edit is reverted (row revert) or the value is
  restored to its saved state.
- It should not require page refresh to become correct.

## Proposed Change

### A) Define authoritative Edited semantics (UI-only)
A row is considered “Edited” if and only if **either** of these is true:

1) **Session edits exist for this GSM** (unsaved edits in the current session), OR
2) **Saved overrides exist for this GSM** on disk.

This allows the pencil icon to represent “this row differs from backend default due to curator action”
including both unsaved and saved.

(If you prefer pencil to mean *only session edits*, implement that instead, but keep it
deterministic. For v1.1, default to (1 OR 2).)

### B) Update Edited status immediately on cell edit
- When any editable field in a row is changed, the Edited pencil icon must appear for that row
  in the same UI session without requiring refresh.

### C) Clear Edited status correctly on revert operations
- “Revert selected row” must:
  - remove session edits for that row
  - recompute the Edited icon
  - if no saved overrides exist for that row, the pencil must disappear
  - if saved overrides still exist, the pencil remains (because the row is still overridden)

- “Clear all edits” must clear all session edits and recompute pencils accordingly.

- “Revert to saved” must:
  - restore values to the saved override state
  - clear session edits
  - pencils remain for rows that have saved overrides, and clear for rows that do not.

- “Discard saved overrides” must:
  - remove saved overrides
  - recompute pencils
  - any row with no remaining session edits must lose the pencil icon.

### D) Ensure AG Grid row model updates on state changes
- After edits/saves/reverts/discards, the AG Grid data passed into the component must be
  regenerated with an updated `is_edited` boolean (or equivalent) per row.
- The Edited column cell renderer must depend only on that `is_edited` value.

No full-page refresh should be required.

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change (policy-spec.md must be updated)

## Acceptance Criteria

- Editing any cell in a row immediately shows a pencil icon in that row.
- Reverting that row (Revert selected row) immediately clears the pencil if there is no saved override.
- Saving overrides does not require Ctrl+R for pencils to reflect the saved state.
- Discarding saved overrides clears pencils for rows that no longer have session edits.
- All behaviors remain UI-only and do not change backend outputs.

## Non-Goals

- Do not change override semantics or file formats.
- Do not add new backend signals.

## Constraints

- UI-only change.
- Keep Edited computation deterministic and testable.

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-130.md` and paste this ticket verbatim.
