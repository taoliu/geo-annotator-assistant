# Ticket #153: Unsaved edits banner persists after overrides are saved

## Background

The curator UI shows a banner indicating “Unsaved edits (session-only)” along with counts of edited GSMs and fields. This banner is intended to reflect local, unsaved UI edits only.

## Problem Statement

After clicking “Save overrides” and successfully persisting overrides to disk, the UI still displays the “Unsaved edits (session-only)” banner with non-zero counts.

This is incorrect and misleading: the edits have already been saved, but the UI continues to treat them as unsaved.

## Proposed Change

Fix UI state synchronization after a successful save:

- After overrides are successfully saved:
  - Clear the session-only edit tracking state
  - Recompute the unsaved edits banner state
- The “Unsaved edits” banner must:
  - appear only when there are local edits not yet saved
  - disappear immediately after a successful save
- Edited GSM and field counts must reflect only unsaved session edits, not persisted overrides.

No backend or persistence behavior changes are required.

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change (policy-spec.md must be updated)

## Acceptance Criteria

- After clicking “Save overrides”:
  - the unsaved edits banner disappears
  - edited GSM and field counts reset to zero
- Reloading the page after saving does not show the unsaved banner.
- Making a new edit after saving correctly shows the banner again.
- Saving again clears the banner reliably.

## Non-Goals

- No changes to override file format.
- No changes to when or how overrides are persisted.
- No changes to backend validation, repair, or decision logic.

## Constraints

- UI-only fix.
- Must not infer unsaved state from backend artifacts.
- Must not clear edits if save fails or is cancelled.

## Guiding Principle

**UI state must reflect reality.**  
A saved edit must never be labeled as unsaved.

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-153.md` and paste this ticket verbatim.
