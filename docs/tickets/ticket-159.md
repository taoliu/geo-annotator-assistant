# Ticket #159: Triage filter state diverges from applied filtering after switching GSE

## Background

The left panel provides triage controls (Decision, Primary failures, Flags) that filter the curation table. Curators expect these controls to remain effective when switching between GSEs during a session.

## Problem Statement

When a curator selects a triage filter (e.g., Decision = FLAGGED) and then switches to another GSE:

- The triage control visually still shows the same selection.
- However, the table behavior indicates the filter is not actually applied (filtering is effectively reset).

This creates a mismatch between displayed UI state and applied filtering.

## Proposed Change

Fix triage filter persistence semantics across GSE switches:

- Define triage filters as session-level UI state (not per-GSE), unless already specified otherwise.
- When active GSE changes, reapply the current triage filter state to the new GSE table.
- Ensure the filtering logic uses the authoritative session-state values, not transient defaults.

No changes to backend artifacts, evidence, or decision semantics.

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change (policy-spec.md must be updated)

## Acceptance Criteria

- Set Decision=FLAGGED, switch to a different GSE:
  - the control still shows FLAGGED
  - and the table is filtered to FLAGGED rows immediately (no extra clicks)
- Same holds for Primary failures and Flags selections.
- Switching back to the original GSE keeps filters applied.
- Clearing filters returns to unfiltered view consistently.

## Non-Goals

- No new filter categories.
- No inference across GSMs or GSEs.
- No persistence to disk; session-only is sufficient.

## Constraints

- UI-only.
- Filtering must continue to respect the invariant: flags and diagnostics come from `evidence.jsonl` only.
- Do not recompute backend decisions; only filter what is already present.

## Guiding Principle

**Displayed state must equal applied state.**

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-159.md` and paste this ticket verbatim.
