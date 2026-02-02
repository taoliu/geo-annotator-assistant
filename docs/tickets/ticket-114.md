# Ticket #114: Add Visual Section Separation and Grouping in Top-Level Layout

## Background

After recent UI improvements, the curator UI surfaces the correct information,
but different conceptual sections visually blend together. This makes the layout
feel dense and harder to scan, even though the content is accurate.

This is a presentation and information-architecture issue only.

## Problem Statement

The top portion of the UI lacks clear visual separation between:
- the GSE identifier,
- GSE-wide summary metadata,
- GSE-wide counts,
- table filters,
- and the curation table.

Headings alone are not sufficient to establish section boundaries.

## Proposed Change (UI Only)

Introduce **lightweight visual separators and grouping** to clearly delineate
major sections, without adding new content or logic.

### 1) Section Grouping

Group the following into distinct visual sections:

1. **GSE Identifier**
   - GSE accession (e.g. “GSE139566”)

2. **GSE-wide Summary**
   - Field-level summary from `gse_field_values.jsonl`
   - GSE-wide counts (Total GSMs, FLAGGED, Overrides, Outliers)
   - Explicit note: “not affected by filters”

3. **Table Controls**
   - Quick filter controls
   - Row count
   - “Table reflects current filters” note

4. **Curation Table**
   - Main GSM table

Each group should be visually distinct.

### 2) Visual Separation Mechanisms

Use one or more of the following (implementation choice left to UI code):

- Horizontal dividers between major sections
- Light container backgrounds or borders
- Increased vertical spacing between sections
- Consistent section header styling

Avoid heavy boxes or high-contrast borders.

### 3) Section Labeling

For each section:
- Use a clear, consistent section header.
- Add a short, muted subtitle where clarification is needed
  (e.g. filter-dependent vs GSE-wide).

## Why No Backend Change Is Required

All changes are layout-only and do not affect data loading, filtering, or
semantics.

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change

## Acceptance Criteria

1. Major conceptual sections are visually distinct at a glance.
2. Users can clearly see where one section ends and the next begins.
3. No data, logic, or interaction behavior changes.
4. UI remains clean and uncluttered.

## Non-Goals

- No redesign of metrics or table content.
- No new summaries or computations.
- No backend changes.

## Constraints

- Keep the design minimal and readable.
- Maintain performance and responsiveness.

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-114.md` and paste this ticket verbatim.
