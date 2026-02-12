# Ticket #171: Remove “Input details” section and merge GSE-wide panels into a single “GSE-wide summary” tab

## Background

Above the curation table, the UI currently shows three collapsible sections:

1. Input details
2. GSE-wide biology (not affected by filters)
3. GSE-wide counts (not affected by filters)

These sections provide metadata and summary statistics.

## Problem Statement

The current layout:

- Uses three separate expanders.
- Duplicates structural framing (separate titles and boxes).
- Consumes vertical space.
- Includes “Input details”, which is rarely needed during normal curation workflow.

This increases scroll distance and fragments related information.

## Proposed Change

1. Remove the “Input details” expander entirely from the main panel.

   - Do not delete the underlying information.
   - It may remain accessible in logs, debug mode, or elsewhere if needed.
   - It should no longer appear in the default curator UI.

2. Merge the remaining two panels into a single section:

   Replace:
   - “GSE-wide biology (not affected by filters)”
   - “GSE-wide counts (not affected by filters)”

   With:
   - A single collapsible section titled:
     **“GSE-wide summary (not affected by filters)”**

3. Inside the merged section:

   - Show the biology summary (data_type, organism, tissue_type, cell_line, disease).
   - Show the counts summary (total GSMs, flagged, overrides, outliers).
   - Maintain visual grouping within the section (e.g., subheadings “Biology” and “Counts”).

4. Preserve the note:
   - “Not affected by filters” must remain clear and visible.

No changes to:

- How summaries are computed.
- Backend-derived semantics.
- Override behavior.
- Export logic.

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change (policy-spec.md must be updated)

## Acceptance Criteria

- “Input details” section is no longer visible in the default UI.
- Only one collapsible section appears above the curation table.
- Biology and counts are both visible within that section.
- The information content remains unchanged.
- The summary continues to ignore session-only edits as before.
- Layout is visually tighter and requires less scrolling.

## Non-Goals

- No change to how summaries are computed.
- No re-derivation of biology from overrides.
- No removal of backend artifacts.

## Constraints

- UI-only change.
- Must not remove required debugging capabilities (if any).
- Must not alter backend-derived values.

## Guiding Principle

**Group related information; remove rarely-used structural overhead.**

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-171.md` and paste this ticket verbatim.
