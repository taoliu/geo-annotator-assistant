# Ticket #109: Fold Non-Essential Summary Text and Remove Inline Help Stub

## Background

After implementing multi-GSE loading and summary panels, the Curator UI now
surfaces more contextual information. While useful, some of this information is
always visible and increases visual noise, especially on wide screens.

Curators primarily need:
- the GSM table,
- decision and override signals,
- quick triage controls.

Secondary context should remain available but not dominate the layout.

## Problem Statement

Several text-heavy sections reduce scanability:

1. The file-loading details shown directly under the
   “GEO GSM Curator UI” title.
2. Verbose textual summaries under “GSE Summary”
   (most common failures, flags, outliers).
3. The inline “> Help” stub above the GSM table, which is not actively used.

These elements are informational but not required for day-to-day curation.

## Proposed Change (UI Only)

### 1) Fold File-Loading Details Under Title

Current (always visible):
- Input root
- Input directory
- Paths to curation/evidence/audit/suggestions

Change:
- Collapse this block by default.
- Replace with a small “Data sources” or “Input details” toggle.
- When expanded, show the same information unchanged.

### 2) Fold Detailed GSE Summary Text

Under “GSE Summary”:

- Keep **high-level counts** always visible:
  - Total GSMs
  - FLAGGED %
  - Overrides
  - Outliers

- Move verbose text into a collapsible section:
  - Most common primary failures
  - Most common flags
  - Outlier categories
  - “Summary reflects current filters” notes

Label example:
- “Show detailed summary”
- Collapsed by default.

No aggregation logic changes.

### 3) Remove Inline “> Help” Stub Above GSM Table

- Remove the “> Help” expandable block above the GSM table.
- Do not replace it with new content.
- Longer help text, if needed, should live in:
  - tooltips (Ticket #103), or
  - documentation (`docs/ui.md`).

## Why No Backend Change Is Required

All changes are presentation-only:
- No data is removed.
- No summaries are recomputed.
- No JSONL inputs or schemas are modified.

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change

## Acceptance Criteria

1. File path details are hidden by default and expandable on demand.
2. GSE Summary shows compact counts by default, with details collapsible.
3. The “> Help” stub above the GSM table is removed.
4. GSM table remains the primary visual focus.
5. No loss of information accessibility.

## Non-Goals

- No redesign of summary metrics.
- No changes to help text elsewhere.
- No backend behavior changes.

## Constraints

- Maintain read-only semantics.
- Preserve determinism and auditability.
- Avoid hiding critical decision signals.

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-109.md` and paste this ticket verbatim.
