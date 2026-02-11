# Ticket #158: Checkbox selection state not persisted on first click

## Background

The curation table includes a checkbox column used to select rows for bulk operations and review. Selection state should update immediately and persist across reruns.

## Problem Statement

When a curator clicks a checkbox:

- The checkmark appears briefly.
- The UI reruns.
- The selection state reverts to the previous state.
- The user must click the checkbox a second time for it to persist.

This indicates that checkbox state is not correctly synchronized with session state before rerender.

## Proposed Change

Fix checkbox state handling to ensure first-click persistence:

1. The checkbox widget must:
   - Be keyed deterministically per row (e.g., using GSM accession).
   - Write directly to `st.session_state`.

2. The authoritative selection state must:
   - Be read directly from session state on rerun.
   - Not depend on transient local variables.

3. Avoid in-place mutation of selection containers.
   - Always reassign updated state to session state.

4. Ensure table rendering uses the authoritative session-state selection set.

No changes to bulk edit semantics or selection logic.

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change (policy-spec.md must be updated)

## Acceptance Criteria

- Clicking a checkbox once immediately persists the checkmark.
- No second click is required.
- Selection state survives reruns triggered by:
  - checkbox click
  - editing other cells
  - sorting
  - filtering
- Bulk edit operations reflect correct selection after one click.

## Non-Goals

- No change to selection meaning.
- No multi-select shortcuts.
- No automatic selection propagation.

## Constraints

- UI-only.
- Must not change backend artifacts.
- Must not introduce race conditions in selection handling.

## Guiding Principle

**Widget state must be authoritative on first interaction.**

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-158.md` and paste this ticket verbatim.
