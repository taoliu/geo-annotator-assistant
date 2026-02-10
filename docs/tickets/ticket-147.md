# Ticket #147: Collapse GSE-wide summary panels by default with explicit expand control

## Background

The GSE-wide biology summary and GSE-wide counts panels are useful for orientation, but during active curation they are rarely consulted. In their current form, they consume significant vertical space and push the curation table further down.

## Problem Statement

High-value summary panels occupy persistent screen space even when the curator is focused on row-level editing. This reduces table visibility and increases scrolling without adding ongoing value.

## Proposed Change

- Collapse the following panels by default:
  - “GSE-wide biology (not affected by filters)”
  - “GSE-wide counts (not affected by filters)”
- Replace each with a compact header row that includes:
  - panel title
  - an explicit expand/collapse toggle
- Preserve current content exactly when expanded.
- Remember expand/collapse state only for the current UI session (no persistence required).

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change (policy-spec.md must be updated)

## Acceptance Criteria

- On initial load, both panels appear collapsed.
- A curator can expand or collapse each panel independently.
- Expanding a panel restores the full existing content without layout breakage.
- No backend data, filters, or summaries are altered.

## Non-Goals

- No removal of summary content.
- No changes to summary computation.
- No persistence of UI state across sessions.

## Constraints

- UI must remain a read-only consumer of backend summaries.
- Collapsing panels must not affect filtering or exports.

## Guiding Principle

**Show context when needed, not constantly.**

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-147.md` and paste this ticket verbatim.
