# Ticket #165: Simplify tooltips for `gse_accession` and `gsm_accession` columns

## Background

All table cells currently display rich diagnostic tooltips containing:

- Displayed value
- Backend value
- LLM original
- Ontology status
- Flags and other metadata

However, for the `gse_accession` and `gsm_accession` columns, this diagnostic content is not meaningful. These fields are identifiers and serve primarily as navigation links to the GEO website.

## Problem Statement

The current tooltip behavior for `gse_accession` and `gsm_accession`:

- Shows unnecessary diagnostic details (LLM value, backend value, etc.).
- Adds visual noise.
- Obscures the primary purpose of these fields: linking to GEO.

This reduces clarity and increases cognitive load without adding value.

## Proposed Change

Change tooltip behavior for the following columns only:

- `gse_accession`
- `gsm_accession`

New tooltip content:

> "Click this accession number to go to GEO website"

Additional requirements:

1. Do not display:
   - LLM original value
   - Backend value
   - Displayed value
   - Ontology diagnostics
   - Flags

2. The cell must remain clickable and continue to link to the appropriate GEO URL.

3. All other columns must retain the existing diagnostic tooltip behavior unchanged.

This is a presentation-only change.

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change (policy-spec.md must be updated)

## Acceptance Criteria

- Hovering over `gse_accession` shows only:
  - "Click this accession number to go to GEO website"
- Hovering over `gsm_accession` shows the same message.
- No diagnostic content is shown for these two columns.
- All other columns retain full diagnostic tooltips.
- GEO navigation still works as before.

## Non-Goals

- No change to link behavior.
- No change to table structure.
- No change to backend artifacts.

## Constraints

- UI-only change.
- Must not remove diagnostic information for other fields.
- Must not interfere with override highlighting or flagged styling.

## Guiding Principle

**Show diagnostics where diagnostics matter; show intent where navigation matters.**

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-165.md` and paste this ticket verbatim.
