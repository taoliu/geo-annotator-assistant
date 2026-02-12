# Ticket #172: Restore session-level triage persistence across GSE switches (regression after navigation/UI refactors)

## Background

Ticket #159 established that triage filters are session-level state. When a curator selects triage filters (e.g., `Decision=FLAGGED`) and switches GSEs, the displayed and applied filtering must remain aligned.

Recent UI refactors (navigation/summary/tooltip work) introduced a regression where triage state can be lost or desynchronized across GSE switches.

## Problem Statement

After switching between GSEs:

- Sidebar triage controls can reset or stop applying as expected.
- Curators lose persistent triage intent (e.g., `FLAGGED`) across GSE navigation.

This reintroduces the Ticket #159 failure mode.

## Proposed Change

1. Add an explicit session-backed triage state object (authoritative store) in `st.session_state`.
2. Hydrate triage widget keys from that state when widget state is missing/invalid.
3. After rendering triage widgets, normalize and persist values back into the authoritative triage state.
4. Continue applying filtering from the normalized authoritative values.

No change to triage semantics, categories, defaults, or backend behavior.

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change (policy-spec.md must be updated)

## Acceptance Criteria

- Set `Decision=FLAGGED`, switch to another GSE:
  - control remains `FLAGGED`
  - table remains filtered to FLAGGED rows immediately
- Primary failures and Flags multiselects persist similarly.
- Switching back to original GSE keeps current session triage state applied.
- No displayed/applied divergence.

## Non-Goals

- No new triage controls.
- No persistence to disk.
- No changes to filtering logic itself.

## Constraints

- UI-only.
- Must be deterministic and session-scoped.
- Must not introduce widget-key mutation errors.

## Guiding Principle

**Displayed triage state must equal applied triage behavior across GSE switches.**
