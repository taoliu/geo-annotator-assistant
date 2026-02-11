# Ticket #156: Simplify export button labels to “GSMs” and “GSEs”

## Background

The redesigned export section introduces two buttons corresponding to the two CSV outputs produced by `geo-gsm-summarize`. The current button labels are verbose and visually heavy, reducing clarity and aesthetic quality.

## Problem Statement

Export buttons currently include too much descriptive text (e.g., “Export GSM CSV (8 fields)”), making them visually noisy and harder to scan. This is unnecessary because the meaning is already explained elsewhere in the UI.

## Proposed Change

Simplify the export button labels:

- Rename buttons to:
  - **“GSMs”**
  - **“GSEs”**
- Move descriptive text to secondary UI locations:
  - Small caption text below the buttons, or
  - Tooltip / hover text, for example:
    - “Export GSM-level CSV (8 canonical fields)”
    - “Export GSE-level CSV (7 fields, summarize output)”

No change to export behavior, semantics, or outputs.

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change (policy-spec.md must be updated)

## Acceptance Criteria

- Export section shows two compact buttons labeled exactly:
  - “GSMs”
  - “GSEs”
- Buttons remain clearly distinguishable and clickable.
- Users can still discover what each export does via tooltip or caption.
- Export outputs remain identical to the current implementation.

## Non-Goals

- No change to CSV formats.
- No change to override application semantics.
- No new export types.

## Constraints

- UI-only change.
- Button labels must remain stable and language-neutral.

## Guiding Principle

**Buttons should name objects; explanations belong elsewhere.**

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-156.md` and paste this ticket verbatim.
