# Ticket #149: Compact bulk edit section with progressive disclosure

## Background

Bulk edit is powerful but infrequently used compared to row-by-row review. In its expanded form, it occupies substantial vertical space even when not actively used.

## Problem Statement

The bulk edit section competes for attention and space even when the curator is not performing bulk operations, increasing visual load.

## Proposed Change

- Collapse the bulk edit section by default into a single-line header:
  - Title: “Bulk edit”
  - Short description: “Apply one value to one column across selected rows”
- Expand the full bulk edit controls only when:
  - the curator clicks the header, or
  - at least one row is selected (optional, UI-only trigger)
- Preserve all existing bulk edit behavior when expanded.

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change (policy-spec.md must be updated)

## Acceptance Criteria

- Bulk edit controls are hidden by default.
- A clear affordance exists to expand and use bulk edit.
- When expanded, functionality and preview behavior are unchanged.
- Collapsing bulk edit does not clear selections or inputs.

## Non-Goals

- No changes to bulk edit semantics or safety checks.
- No automatic bulk actions.

## Constraints

- Bulk edit must remain explicit and reversible.
- UI state does not need to persist across reloads.

## Guiding Principle

**Power tools should be available, not dominant.**

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-149.md` and paste this ticket verbatim.
