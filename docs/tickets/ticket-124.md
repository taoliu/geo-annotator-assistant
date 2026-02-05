# Ticket #124: Do not treat FALLBACK ontology status as a flagged cell condition

## Background

Cell-level highlighting in the AG Grid table is intended to surface curator-facing
warnings based on explicit evidence flags.

Currently, fields with `ontology_status = FALLBACK` but no evidence flags are being
incorrectly highlighted and included in `flagged_fields`.

This conflates terminal fallback decisions with curator warning signals.

## Problem Statement

Fields with:
- `ontology_status = FALLBACK`
- `flags = []`

are being treated as flagged, causing incorrect cell highlighting and misleading
`flagged_fields` display.

This violates the intended distinction between:
- fallback (acceptable terminal state)
- flagged (requires curator attention)

## Correct Highlighting Rule (Authoritative)

A cell in an essential biology column must be highlighted **if and only if**:
`len(evidence_by_field[field].flags) > 0`


All other signals must be ignored for highlighting purposes.

## Proposed Change

### A) Fix cell highlighting logic
- Update AG Grid `cellClassRules` to depend **only** on the per-field evidence flags list.
- Explicitly ignore:
  - `ontology_status`
  - `terminal_fallback`
  - `attempts`
  - summary `flagged_fields`

### B) Fix flagged_fields display (UI-only)
- Ensure the `flagged_fields` column (if shown) is derived from:
  - union of fields where `evidence_by_field[field].flags` is non-empty
- Do not include fields that are FALLBACK-only.

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change (policy-spec.md must be updated)

## Acceptance Criteria

- In the provided example GSM5320850:
  - `tissue_type` cell is highlighted
  - `cell_line` and `disease` cells are NOT highlighted
- `flagged_fields` contains only `tissue_type`
- Fields with `FALLBACK` but no flags never highlight
- Behavior is stable across reruns and filters

## Non-Goals

- Do not reinterpret ontology_status semantics.
- Do not introduce new flags or downgrade fallback behavior.

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-124.md` and paste this ticket verbatim.
