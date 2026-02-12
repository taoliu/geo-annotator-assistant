# Ticket #168: Sync “Active GSE” dropdown value when navigating via Prev/Next

## Background

The sidebar provides two ways to change the active GSE:

- Selecting from the “Active GSE” dropdown
- Using Prev/Next buttons

Both should represent the same underlying “active GSE” state.

## Problem Statement

When navigating using Prev/Next:

- The main panel updates to the new GSE (correct).
- The sidebar “Active GSE” dropdown does not update to reflect the new active GSE (incorrect).

This causes a mismatch between displayed UI state and the actual active GSE being curated.

## Proposed Change

Unify and synchronize active GSE state:

1. Maintain a single authoritative session-state variable for active GSE (e.g., `st.session_state["active_gse"]`).

2. Prev/Next buttons must update this authoritative state.

3. The “Active GSE” dropdown must be bound to the same authoritative state, so that:
   - Selecting from dropdown updates `active_gse`
   - Prev/Next updates `active_gse`
   - The dropdown display always reflects `active_gse` after rerun

4. Ensure no rerun ordering bug:
   - After Prev/Next click, the dropdown must show the updated value on the very next render.

No change to:
- GSE ordering
- Which GSEs are available
- Backend loading semantics

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change (policy-spec.md must be updated)

## Acceptance Criteria

- Clicking Prev changes:
  - main panel GSE title
  - sidebar dropdown selection
  to the same new GSE.
- Clicking Next changes both similarly.
- Selecting a GSE from the dropdown also updates the main panel correctly.
- No mismatch can occur between dropdown value and main panel title during normal navigation.
- Works across multiple consecutive Prev/Next clicks.

## Non-Goals

- No new navigation behaviors.
- No persistence of active GSE across reloads unless already present.

## Constraints

- UI-only.
- Must not introduce infinite rerun loops.
- Must preserve existing filtering/triage behavior unless separately specified.

## Guiding Principle

**There must be exactly one source of truth for active GSE.**

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-168.md` and paste this ticket verbatim.
