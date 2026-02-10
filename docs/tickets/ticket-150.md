# Ticket #150: Compact overrides and exports sections into collapsible panels

## Background

The “Overrides (persistent)” and “Exports” sections are important but typically consulted only at specific workflow stages (reviewing edits or exporting final results).

## Problem Statement

These sections consume vertical space continuously, even when no overrides exist or exports are not imminent.

## Proposed Change

- Collapse both sections by default:
  - “Overrides (persistent)”
  - “Exports”
- Show a concise summary line when collapsed:
  - Overrides: edited GSM count and field count
  - Exports: short description (“Apply overrides, no revalidation”)
- Expand on user click.

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change (policy-spec.md must be updated)

## Acceptance Criteria

- Both sections load collapsed by default.
- Summary information remains visible when collapsed.
- Expanded view preserves current content and behavior exactly.
- Export actions remain explicit and unchanged.

## Non-Goals

- No changes to export format or logic.
- No automatic export triggers.

## Constraints

- Overrides and export semantics must remain transparent and auditable.
- No hidden side effects from collapsing.

## Guiding Principle

**Defer infrequent actions until the user asks for them.**

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-150.md` and paste this ticket verbatim.
