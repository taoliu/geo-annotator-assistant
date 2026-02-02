# Ticket #115: Final Layout Density Tuning and Section Consolidation

## Background

The curator UI now presents the correct information, but layout density and
visual grouping still need refinement. Excess whitespace and mixed semantic
layers make the interface feel sparse and less intuitive.

This ticket focuses purely on layout tightening and visual hierarchy.

## Problem Statement

1) Excess vertical whitespace separates sections more than necessary.
2) GSE-wide biology fields and GSE-wide metrics are not visually separated.
3) Explanatory text about filter scope is redundant and adds noise.
4) The “Curation table” section header appears twice.

## Proposed Change (UI Only)

### 1) Reduce Excess Whitespace

- Tighten vertical spacing between sections.
- Avoid large empty gaps between headers and content.
- Use spacing intentionally only to separate major conceptual blocks.

### 2) Box GSE-Wide Biology Fields

Group the following GSE-wide field values into a single compact visual box/card:

- data_type
- organism
- tissue_type
- cell_line
- disease

Label the box clearly:
- “GSE-wide biology (not affected by filters)”

This box should be visually distinct from metric counts.

### 3) Separate GSE Metrics from Biology

Display GSE-wide metrics in a separate compact row below the biology box:

- Total GSMs
- FLAGGED (count and percent)
- Overrides
- Outliers

Do not repeat these values elsewhere on the page.

### 4) Remove Redundant Explanatory Text

Remove the following text blocks entirely:
- “Filters apply to table only”
- “Table reflects current filters”

The layout already makes this clear.

### 5) Remove Duplicate “Curation table” Header

- Keep a single “Curation table” section header above the actual table.
- Remove any secondary or explanatory “Curation table” labels.

## Why No Backend Change Is Required

All changes are presentation-only and do not affect data, logic, or behavior.

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change

## Acceptance Criteria

1. The UI shows visibly reduced empty space without feeling cramped.
2. GSE-wide biology fields appear in a single boxed section.
3. GSE-wide metrics appear once, clearly separated from biology fields.
4. Redundant filter explanatory text is removed.
5. Only one “Curation table” header remains.

## Non-Goals

- No new data fields.
- No new summaries or calculations.
- No backend changes.

## Constraints

- Maintain readability.
- Preserve performance and determinism.
- Keep the UI minimal and curator-focused.

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-115.md` and paste this ticket verbatim.
