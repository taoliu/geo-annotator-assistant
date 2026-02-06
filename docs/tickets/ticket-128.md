# Ticket #128: Group override persistence controls with table edit controls

## Background

Curators frequently use both:
- session edit controls (Revert selected row, Clear all edits)
and
- override persistence controls (Save overrides, Revert to saved, Discard saved overrides)

When these controls are separated on the page, it increases navigation and creates
avoidable mistakes during long curation sessions.

## Problem Statement

Override persistence buttons (“Save overrides”, “Revert to saved”, “Discard saved overrides”)
are not colocated with the primary edit controls (“Revert selected row”, “Clear all edits”).
This increases friction and makes the workflow harder to understand.

## Proposed Change

Move the following buttons:

- Save overrides
- Revert to saved
- Discard saved overrides

to be grouped together with:

- Revert selected row
- Clear all edits

Placement requirement:
- Either place all five buttons in a single grouped control bar directly above the
  curation table, OR place the override persistence buttons immediately adjacent to
  the existing edit control buttons at the top of the curation table content.

Layout requirements:
- Keep the group visually coherent (single row or two compact rows).
- Maintain existing button behavior and safety confirmations (if any).
- Do not change override semantics or persistence timing.

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change (policy-spec.md must be updated)

## Acceptance Criteria

- The override persistence controls are colocated with the main table edit controls.
- Button order and grouping are intuitive (save/revert/discard near edit controls).
- No functional behavior changes:
  - Save overrides writes the same overrides artifact as before.
  - Revert to saved restores the same saved state as before.
  - Discard saved overrides performs the same destructive action as before.
- No backend artifacts are modified beyond the existing overrides persistence behavior.

## Non-Goals

- Do not add new buttons or new persistence features.
- Do not change export behaviors.
- Do not redesign confirmation dialogs beyond repositioning.

## Constraints

- UI-only change.
- Preserve determinism and auditability of user-triggered persistence actions.

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-128.md` and paste this ticket verbatim.
