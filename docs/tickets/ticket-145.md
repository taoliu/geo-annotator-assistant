# Ticket #145: Bulk edit preview panel with explicit selection feedback

## Background

Bulk edit exists and is correctly described as explicit and reversible. However, the current preview is a single-line text summary that is easy to miss and does not provide strong confidence about what will change before clicking “Apply”.

This is most noticeable when curators select many rows and want assurance that the intended rows/column/value combination is correct.

## Problem Statement

Bulk edit currently lacks a strong pre-apply confirmation experience:

- The preview summary is visually subtle.
- There is no clear visual linkage between selected rows and the pending bulk operation.
- Curators may hesitate or make mistakes due to low confidence before applying changes.

## Proposed Change

Enhance the bulk edit UI with a dedicated preview panel (UI-only):

1. Preview panel (always visible when a column is selected):
   - Selected row count
   - Target column
   - New value (or “(empty)” if blank)
   - Count of rows that would change vs rows that would be no-ops

2. Optional sample preview (bounded, UI-only):
   - Show up to N (e.g., 5–10) example GSM accessions from the current selection with:
     - old value → new value
     - indicate no-op rows explicitly

3. Selection feedback:
   - When bulk edit inputs are valid (column selected + value provided + at least one row selected), show a clear “Ready to apply” state.
   - When not valid, show a clear “Missing: …” state.

No changes to bulk edit semantics:
- Apply still requires explicit click.
- No implicit selection expansion.
- Revert behavior remains unchanged.

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change (policy-spec.md must be updated)

## Acceptance Criteria

- Bulk edit area shows a clear preview panel that updates immediately when:
  - selection changes
  - target column changes
  - new value changes
- Preview panel correctly reports:
  - selected row count
  - change count
  - no-op count
- Sample preview (if implemented) is bounded to a small number of rows and does not slow the UI noticeably.
- Apply remains disabled unless the bulk edit operation is valid (as currently).
- No changes to export output unless curator explicitly applies bulk edits and saves overrides.

## Non-Goals

- No backend changes.
- No new validation, ontology grounding, or policy interpretation in the UI.
- No auto-apply or inferred bulk actions.

## Constraints

- All per-field diagnostics and “needs attention” cues must remain sourced from `evidence.jsonl` only.
- Bulk edit must remain explicit, reversible, and auditable (overrides persisted only via user action).

## Guiding Principle

**Bulk actions must be safe by design.**  
Stronger preview and feedback reduce curator error without changing semantics.

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-145.md` and paste this ticket verbatim.
