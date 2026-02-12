# Ticket #173: Fix Streamlit widget-key mutation error in triage controls (post-widget session assignment)

## Background

Ticket #172 introduced a session-backed authoritative triage state to restore persistence across GSE switches.

## Problem Statement

Streamlit raises:

`st.session_state.triage_decision_filter cannot be modified after the widget with key triage_decision_filter is instantiated.`

Cause: `_render_triage_controls` writes widget-bound session keys after rendering `selectbox`/`multiselect`/`checkbox` widgets.

## Proposed Change

1. Keep pre-widget hydration of widget keys (valid in Streamlit).
2. After widget render, persist only the authoritative `triage_state` object.
3. Do not assign any widget-bound keys (`triage_decision_filter`, `triage_primary_filter`, `triage_flag_filter`, `triage_sort_by`, `triage_sort_desc`) in the post-widget phase.

No change to triage semantics, defaults, or filtering behavior.

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change (policy-spec.md must be updated)

## Acceptance Criteria

- App no longer raises StreamlitAPIException for triage widget keys.
- Triage state remains persistent across GSE switches (Ticket #159/#172 intent preserved).
- Displayed triage controls and applied filtering remain aligned.

## Non-Goals

- No new triage filters or sorting modes.
- No backend changes.

## Constraints

- UI-only.
- Must preserve deterministic session behavior.

## Guiding Principle

**Never mutate Streamlit widget keys after widget instantiation; persist authoritative state separately.**
