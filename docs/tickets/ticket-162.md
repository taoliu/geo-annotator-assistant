# Ticket #162: Move secondary action buttons into “More actions” to reduce header clutter

## Background

The main action area above the curation table currently displays multiple buttons:

- Save overrides
- Revert selected row
- Clear all edits
- More actions (expander)

While all actions are valid, not all are primary. Only “Save overrides” is used frequently during normal curation flow.

## Problem Statement

Displaying all action buttons persistently:

- Increases visual clutter
- Competes with primary action (“Save overrides”)
- Consumes horizontal and vertical space
- Reduces perceived hierarchy

Secondary actions should not dominate the main workflow area.

## Proposed Change

Restructure the action area as follows:

1. Keep “Save overrides” as the only always-visible primary button.

2. Move the following actions into the existing “More actions” expander:
   - Revert selected row
   - Clear all edits

3. Inside “More actions”, present secondary actions clearly separated from any informational content.

4. Do not change the behavior, confirmation dialogs, or semantics of these actions.

This is a layout-only refactor.

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change (policy-spec.md must be updated)

## Acceptance Criteria

- Only “Save overrides” is visible in the main header area by default.
- “Revert selected row” and “Clear all edits” are accessible under “More actions”.
- Clicking these buttons behaves exactly as before.
- No change to override persistence semantics.
- No regression in save/undo behavior.

## Non-Goals

- No new confirmation dialogs.
- No change to button wording.
- No change to override logic.
- No removal of any action.

## Constraints

- UI-only change.
- Must preserve current confirmation safeguards.
- Must not change state tracking or unsaved detection logic.

## Guiding Principle

**Primary actions should dominate; secondary actions should not compete.**

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-162.md` and paste this ticket verbatim.
