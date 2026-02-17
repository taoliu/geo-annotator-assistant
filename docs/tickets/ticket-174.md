# Ticket #174: Add curator tooltips for all action buttons in the curation header and “More actions”

## Background

The curation table header area contains multiple curator actions (buttons). These actions affect either session edits or persistent overrides and should be self-explanatory at point of use.

Currently, only the “Bulk edit” button has a tooltip.

## Problem Statement

Most action buttons have no tooltip guidance, which can confuse curators about:

- Scope (visible rows vs selected row)
- Persistence (session-only vs saved overrides)
- Risk (discarding saved overrides)
- Reversibility

This increases hesitation and risk of misuse.

## Proposed Change

Add short, consistent tooltips to all curator-facing action buttons in this area:

### Header actions
- **Check all**: “Mark all visible rows as checked (reviewed).”
- **Uncheck all**: “Clear the checked marker for all visible rows.”
- **Save overrides**: “Persist current edits as curator overrides for this GSE.”
- **Bulk edit**: keep existing tooltip (ensure it is concise and consistent).

### “More actions” section
Session edit actions:
- **Revert selected row**: “Undo session edits for the currently selected row (does not change saved overrides).”
- **Clear all edits**: “Undo all session edits for this GSE (does not change saved overrides).”

Saved override actions:
- **Revert to saved**: “Reload the last saved overrides (discard current session edits).”
- **Confirm discard saved overrides** (checkbox label): “Required confirmation before deleting saved overrides.”
- **Discard saved overrides**: “Delete saved overrides for this GSE (irreversible).”

Requirements:
- Tooltips must not change semantics or behavior.
- Tooltips must be phrased simply and consistently.
- For destructive actions, tooltips must explicitly mention irreversibility.

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change (policy-spec.md must be updated)

## Acceptance Criteria

- Every button listed above shows an appropriate tooltip on hover.
- Tooltips accurately describe scope and persistence.
- No layout changes are required (tooltips only).
- No behavioral changes to actions.

## Non-Goals

- No new confirmation dialogs.
- No changes to action availability or enable/disable logic.
- No changes to backend artifacts.

## Constraints

- UI-only.
- Tooltips must not obstruct clicking or editing.
- Keep tooltip text short (one sentence preferred).

## Guiding Principle

**Explain actions at the point of action without adding clutter.**

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-174.md` and paste this ticket verbatim.
