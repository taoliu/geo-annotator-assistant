# Ticket #166: Remove bottom “Overrides (persistent)” and “Exports” collapsed sections below the curation table

## Background

Below the curation table, the UI currently displays two collapsed sections:

- “Overrides (persistent)”
- “Exports”

These sections duplicate or partially overlap with functionality that is already accessible elsewhere in the interface (e.g., Save overrides button and sidebar export buttons).

## Problem Statement

The two bottom collapsed sections:

- Consume vertical space even when collapsed.
- Duplicate export functionality already available in the sidebar.
- Provide override visibility that is not required in the main workflow.
- Increase visual complexity without adding primary workflow value.

This makes the page longer and less focused.

## Proposed Change

Remove the following sections entirely from below the curation table:

1. “Overrides (persistent)”
2. “Exports”

Requirements:

- Do not remove override persistence functionality.
- Do not remove export functionality.
- Ensure export remains available via the sidebar “GSMs” and “GSEs” buttons.
- Ensure override saving remains available via “Save overrides”.

This is a layout cleanup only.

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change (policy-spec.md must be updated)

## Acceptance Criteria

- The two collapsed sections no longer appear below the curation table.
- Override saving behavior remains unchanged.
- Export functionality remains available via sidebar buttons.
- No backend artifacts or override files are affected.
- No regressions in override persistence.

## Non-Goals

- No change to override semantics.
- No change to export semantics.
- No change to CLI behavior.

## Constraints

- UI-only change.
- Must not remove any underlying data structures.
- Must not affect session-state tracking.

## Guiding Principle

**Remove duplication; keep a single clear path for each action.**

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-166.md` and paste this ticket verbatim.
