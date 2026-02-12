# Ticket #169: Make Bulk edit a temporary mode that auto-resets and closes after “Apply to selected”

## Background

Bulk edit is an explicit operation that applies one value to one column across selected rows. After applying, curators typically return to review/edit individual rows. Leaving the full bulk edit UI expanded after an apply increases visual clutter and can encourage accidental repeat operations.

## Problem Statement

Currently, after clicking “Apply to selected”, the bulk edit UI remains active and retains prior inputs (target column, new value, previews). This is not the desired workflow. The curator expects bulk edit to behave like a temporary mode:

- Activate bulk edit explicitly
- Apply once
- Automatically exit and reset

## Proposed Change

1. Replace the current “Bulk edit” toggle with a button-like control:
   - Label: “Bulk edit”
   - Clicking it enters “Bulk edit mode” and reveals the bulk edit UI.

2. After a successful “Apply to selected”:
   - Exit bulk edit mode automatically (hide the bulk edit UI).
   - Reset bulk edit inputs to defaults:
     - target column cleared
     - new value cleared
     - previews cleared
   - Return to inactive state immediately on the next render.

3. Failure behavior:
   - If apply fails (validation/UI-side error), do not auto-close.
   - Keep UI open so the curator can correct the issue.

4. The change must not alter bulk edit semantics:
   - Still explicit
   - Still reversible (via existing override mechanisms)
   - No implicit saving

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change (policy-spec.md must be updated)

## Acceptance Criteria

- Bulk edit is inactive by default and appears as a single “Bulk edit” button/control.
- Clicking “Bulk edit” activates the mode and shows the full bulk edit UI.
- After clicking “Apply to selected” and succeeding:
  - bulk edit UI closes automatically
  - target column, value, and previews are reset
  - the UI returns to the inactive state
- After a failed apply:
  - bulk edit UI remains open
  - inputs are preserved for correction
- No change to the actual edits applied.

## Non-Goals

- No changes to selection behavior.
- No auto-saving overrides after apply.
- No changes to repair/validation logic.

## Constraints

- UI-only.
- Must avoid leaving stale bulk edit state in session state.
- Must work reliably across reruns.

## Guiding Principle

**Bulk edit is a deliberate one-shot operation, not a persistent mode.**

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-169.md` and paste this ticket verbatim.
