# Ticket #152: Keyboard navigation for GSE selector (next/previous)

## Background

Curators often review GSEs sequentially. Mouse-driven dropdown navigation is slow and repetitive for this workflow.

## Problem Statement

There is no fast way to move to the next or previous GSE without reopening the dropdown and scrolling.

## Proposed Change

Enhance the GSE selector with keyboard navigation:

- When the GSE selector is focused:
  - `ArrowDown` selects the next GSE in the list
  - `ArrowUp` selects the previous GSE in the list
- Selection change should:
  - immediately load the new GSE
  - preserve all existing UI semantics

Optional (nice-to-have, not required):
- Display a subtle hint tooltip: “Use ↑ / ↓ to navigate GSEs”

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change (policy-spec.md must be updated)

## Acceptance Criteria

- Arrow keys move between GSEs without opening the dropdown.
- Navigation respects the existing GSE ordering.
- No accidental multi-step jumps or skipped GSEs.

## Non-Goals

- No wraparound behavior unless explicitly implemented.
- No new shortcuts outside the GSE selector focus.

## Constraints

- UI-only behavior.
- Must not bypass confirmation or trigger unintended bulk actions.

## Guiding Principle

**Frequent navigation paths deserve keyboard support.**

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-152.md` and paste this ticket verbatim.
