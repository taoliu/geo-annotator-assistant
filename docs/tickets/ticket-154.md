# Ticket #154: Move “Unsaved edits” status indicator below the “Save overrides” button

## Background

The UI currently shows an “Unsaved edits (session-only)” banner near the top of the main panel. This is accurate but visually prominent and consumes vertical space. The most relevant place for this status is near the action that resolves it: “Save overrides”.

## Problem Statement

The unsaved status is separated from the save action, which creates unnecessary visual noise and forces the curator to scan the page to confirm whether saving is needed.

## Proposed Change

- Remove the large “Unsaved edits (session-only)” banner from the top area of the main panel.
- Add a compact status line directly below the “Save overrides” button that shows:
  - “No unsaved edits” (when clean), or
  - “Unsaved edits: Edited GSMs: X; Edited fields: Y” (when dirty)
- Keep the meaning unchanged:
  - counts reflect session-only edits not yet saved
  - persisted overrides are not labeled “unsaved”
- Optional UI detail (non-semantic):
  - Use subtle styling (small text) and color only for emphasis, without competing with flagged/override cell colors.

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change (policy-spec.md must be updated)

## Acceptance Criteria

- When there are unsaved edits, the status line appears below “Save overrides” with correct counts.
- After successful save, the status line updates immediately to “No unsaved edits” (or disappears).
- The top-of-panel banner is no longer shown.
- No changes to override persistence semantics, export behavior, or table editing behavior.

## Non-Goals

- No change to when edits are considered “unsaved”.
- No auto-save behavior.
- No changes to backend artifacts.

## Constraints

- UI-only change.
- Must remain consistent with the existing session-state tracking for edits and save success/failure handling.
- If save fails, the status must continue to show unsaved edits.

## Guiding Principle

**Put status next to the action that resolves it.**

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-154.md` and paste this ticket verbatim.
