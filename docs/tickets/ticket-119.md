# Ticket #119: Explicitly mark GSE-wide biology panel as backend-derived and edit-independent

## Background

The “GSE-wide Biology (Not affected by filters)” panel summarizes backend-derived
biology fields for a GSE.

During active curation sessions, curators may apply session-only edits to GSM-level
biology fields. Currently, the GSE-wide biology panel does not reflect these edits,
but this behavior is not made explicit in the UI.

This creates potential curator confusion and false confidence.

## Problem Statement

The GSE-wide biology panel appears visually authoritative but silently ignores
session edits. Curators cannot tell whether the summary reflects edited state
or original backend outputs.

This is a UI clarity issue, not a backend or policy issue.

## Proposed Change

Make the backend-only nature of the GSE-wide biology panel **explicit and visible**.

UI changes:

1. Add a clear, persistent label in the panel header indicating:
   - The panel is derived from backend outputs
   - It is not affected by session edits

   Example phrasing (exact wording may vary):
   > “Backend-derived summary (ignores session edits)”

2. When session edits exist that touch any biology field
   (`data_type`, `organism`, `tissue_type`, `cell_line`, `disease`):
   - Display a subtle, non-blocking visual indicator (e.g. icon or muted note)
   - No recomputation or value change occurs

3. The displayed values remain exactly as currently implemented.

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change (policy-spec.md must be updated)

## Acceptance Criteria

- The GSE-wide biology panel explicitly states it is backend-derived.
- The statement is always visible, not hidden in help text.
- When session edits exist, the panel does NOT change values.
- No aggregation, recomputation, or inference is introduced.
- Backend artifacts and schemas are untouched.

## Non-Goals

- Do not recompute GSE-wide biology based on edits.
- Do not introduce majority vote, union, or override logic.
- Do not change backend JSONL generation.
- Do not add new biology fields.

## Constraints

- UI-only change.
- Backend output remains the source of truth.
- Semantics must be obvious at a glance during long curation sessions.

## Guiding Principle

UI clarity and curator trust outweigh convenience.
Backend output is authoritative; the UI must not blur that boundary.

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-119.md` and paste this ticket verbatim.
