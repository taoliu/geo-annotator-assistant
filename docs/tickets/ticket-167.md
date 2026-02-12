# Ticket #167: Add “Check all / Uncheck all” control for curator review checkbox column

## Background

The curation table includes a curator “checked” column (second column) used as a review-completion marker per row. Curators currently toggle this checkbox row-by-row.

## Problem Statement

For workflows where a curator wants to mark many rows as reviewed (or reset them), row-by-row toggling is slow. There is no fast way to:

- Mark all currently visible rows as checked
- Clear checked state for all currently visible rows

This increases repetitive clicking, especially after filtering to a subset (e.g., Needs attention).

## Proposed Change

Add a “Check all / Uncheck all” control for the curator review checkbox column.

Requirements:

1. Provide a header-level control in the “checked” column header:
   - Action: “Check all visible”
   - Action: “Uncheck all visible”
   (This can be implemented as a single tri-state checkbox or two small buttons.)

2. Scope:
   - Applies only to rows currently visible in the table after filters/search/triage.
   - Must not affect rows hidden by current filters.

3. Persistence:
   - The checked markers must persist in the same way as current per-row checked behavior (existing mechanism).
   - Must update immediately on first click (no double-click requirement).

4. Safety:
   - This is an explicit curator action only.
   - No automatic checking based on flags, overrides, or decisions.

No changes to:
- row selection semantics (if any separate selection exists)
- overrides
- backend artifacts or policy logic

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change (policy-spec.md must be updated)

## Acceptance Criteria

- A header-level control exists for the curator “checked” column.
- “Check all visible” marks every visible row as checked.
- “Uncheck all visible” clears the checked marker for every visible row.
- Works correctly under:
  - quick filters (All / Needs attention / Has overrides / Clean)
  - sidebar filters/triage
  - sorting
  - switching GSEs (checked state remains correct per existing persistence rules)
- No impact on override state or export outputs.

## Non-Goals

- No inference of “checked” from other signals.
- No automatic marking on save/export.
- No changes to backend decision routing.

## Constraints

- UI-only change.
- Must reuse existing checked-marker persistence mechanism.
- Must avoid slow per-row reruns when applying to large visible sets (batch update in UI state).

## Guiding Principle

**Review markers should support batch marking, but only by explicit curator action.**

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-167.md` and paste this ticket verbatim.
