# Ticket #163: Show table row count as a compact badge next to “Curation table”

## Background

The UI shows the current number of visible rows (after filters/triage) as a separate “Rows: N” line near the curation table header.

## Problem Statement

“Rows: N” currently consumes its own vertical line, which reduces visible table space and adds unnecessary visual weight for a simple scalar indicator.

## Proposed Change

- Remove the standalone “Rows: N” line.
- Display the row count as a compact badge next to the “Curation table” header, for example:
  - `Curation table  [Rows: 6]`
- The count must reflect the same value as today (the number of rows currently shown in the table view after applied filters/triage).
- This is presentation-only; no changes to filtering or counting logic.

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change (policy-spec.md must be updated)

## Acceptance Criteria

- “Rows: N” no longer appears as a separate line.
- A compact row-count badge appears on the same line as the “Curation table” title.
- The row count remains correct under:
  - search filtering
  - triage filtering (Decision, Primary failures, Flags)
  - sorting changes
  - switching GSEs
- No changes to table behavior or data.

## Non-Goals

- No changes to what “row count” means.
- No new metrics (e.g., total rows vs filtered rows) unless already present.
- No styling changes outside the header area.

## Constraints

- UI-only.
- Must not introduce layout jitter when the count changes.

## Guiding Principle

**Use compact indicators for compact information.**

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-163.md` and paste this ticket verbatim.
