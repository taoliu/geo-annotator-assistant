# Ticket #129: Progressive disclosure for override persistence actions (collapse low-frequency + destructive controls)

## Background

Override persistence controls are currently displayed as separate prominent buttons
near the curation table. This creates visual clutter and increases curator hesitation,
because low-frequency and destructive actions are always visible.

Curators primarily need “Save overrides” visible, while “Revert to saved” and
“Discard saved overrides” should be available but not visually dominant.

## Problem Statement

The override persistence actions are:
- conceptually different from session edit controls
- low frequency compared to normal editing
- include destructive actions

Showing all of them at once is distracting and harms ergonomics.

## Proposed Change

Implement progressive disclosure for override persistence actions:

### A) Keep only “Save overrides” always visible
- “Save overrides” remains a primary button in the control bar above the table.

### B) Move “Revert to saved” and “Discard saved overrides” under a collapsible section
- Add a compact secondary control next to “Save overrides”, e.g.:
  - “More ▾” button OR a Streamlit expander labeled “More actions”
- Inside this section, place:
  - “Revert to saved”
  - “Discard saved overrides” (destructive)

### C) Keep destructive confirmation inside the collapsed section
- The “Confirm discard saved overrides” checkbox remains required.
- The checkbox and destructive button must be colocated inside the expanded area.
- When the section is collapsed, the destructive action must not be visible.

### D) Preserve existing behavior
- No changes to what each action does.
- No changes to override file format, persistence timing, or safety rules.
- Only UI layout and visibility changes.

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change (policy-spec.md must be updated)

## Acceptance Criteria

- “Save overrides” is visible by default above the curation table.
- “Revert to saved” and “Discard saved overrides” are not visible unless the user
  expands “More actions” (or equivalent).
- The discard confirmation checkbox is only shown inside the expanded section and is
  required to enable the discard action (same safety as current UI).
- All actions behave exactly as before.

## Non-Goals

- Do not remove any functionality.
- Do not change button wording unless needed for clarity.
- Do not add new persistence features.

## Constraints

- UI-only change.
- Keep controls grouped near the curation table, consistent with Ticket #128.

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-129.md` and paste this ticket verbatim.
