# Ticket #131: Fix stale AG Grid state by introducing explicit table model ownership + grid remount versioning (eliminate Ctrl+R dependency)

## Background

After migrating the curation table to AG Grid, multiple UI state changes (notably the
“Edited” pencil indicator) do not appear unless the curator clicks “Save overrides”
and manually hard-refreshes the page (Ctrl+R).

This indicates the UI is suffering from stale component state and/or stale cached
dataflow: Streamlit reruns are not resulting in the AG Grid component rendering the
latest row model.

This is a UI wiring issue. Backend behavior is unchanged.

## Problem Statement

Current symptoms:
- Pencil/edited status does not update live after cell edits.
- Pencil/edited status does not clear reliably after revert actions.
- UI appears to require Ctrl+R to reflect state changes.

Likely causes (one or more):
- AG Grid component not being re-mounted when the table model changes.
- Dataframe/state mutated in place, preventing Streamlit from detecting changes.
- Cached loader/assembler returning stale table data.
- Missing explicit rerun after state transitions.

## Proposed Change

Implement a robust Streamlit + AG Grid best-practice state pattern:

### A) Establish a single source of truth for the table row model
- Maintain the table dataframe in `st.session_state["table_df"]`.
- All UI edits and actions (edit cell, revert, clear edits, save, discard) must update
  `table_df` (via replacement, not in-place mutation).
- Compute a boolean column `is_edited` in `table_df` that drives the pencil icon.

### B) Avoid in-place mutation (required)
- Any update to `table_df` must be performed by creating a new dataframe object
  (deep copy) and reassigning it to session_state.

### C) Introduce explicit grid remount versioning (key-based remount)
- Add `st.session_state["grid_version"]` (int, starts at 0).
- Any action that should refresh the grid must increment `grid_version`.
- Pass a grid component key that includes this version, e.g.:
  `key=f"curation_grid_{grid_version}"`

This forces the AG Grid component to remount and display the updated model without
requiring Ctrl+R.

### D) Ensure edits flow from AG Grid back into the table model
- Configure AG Grid to return edited data immediately (not only on save).
- After a cell edit is detected, update `st.session_state["table_df"]` and recompute
  `is_edited`.
- Increment `grid_version` and trigger `st.rerun()` (or equivalent) so the UI redraws
  with correct pencil state.

### E) Remove or disable caching that can stale the table model (during fix)
- Audit any `st.cache_data` / memoization used by functions that feed the curation table.
- During this ticket, disable caching in the table assembly path or add explicit cache
  keys tied to `grid_version` / file mtimes so updates are reflected immediately.

### F) Add targeted debug instrumentation (temporary)
Add temporary debug output (guarded by a UI-only debug flag) to verify correct wiring:
- `grid_version`
- `id(table_df)` (object identity)
- count of `is_edited == True`

This must not be enabled by default in normal curator mode.

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change (policy-spec.md must be updated)

## Acceptance Criteria

- After editing any cell, the pencil icon appears immediately without clicking “Save overrides”.
- After reverting a row or clearing edits, the pencil icon updates immediately without Ctrl+R.
- After saving overrides, the UI reflects saved state immediately without Ctrl+R.
- After discarding saved overrides, the UI reflects the new state immediately without Ctrl+R.
- No backend artifacts or schemas are changed.
- AG Grid remains the table component; this is a wiring/state fix only.

## Non-Goals

- No new curator features.
- No changes to override semantics, validation, repair, or backend decisions.
- No redesign of table layout beyond what is required for correct state refresh.

## Constraints

- UI-only change.
- The solution must be deterministic and testable.
- Prefer minimal code changes localized to the UI table assembly + AG Grid wrapper.

## Implementation Notes (for Codex)

Codex must locate and update:
- the function that assembles the dataframe for the AG Grid table
- the AG Grid invocation (ensure `key` includes `grid_version`)
- handlers for edit/revert/save/discard actions (increment version + rerun)
- any caching that touches the table assembly path

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-131.md` and paste this ticket verbatim.
