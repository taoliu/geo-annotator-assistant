# Ticket #116: Final Page Header Simplification and Curation Table Panel Consolidation

## Background

After iterative UI improvements, the curator page still contains structural
redundancies inherited from earlier layouts. These now distract from the core
workflow rather than helping it.

This ticket finalizes the page hierarchy so that the GSE itself is the primary
context, and the curation table is the central working surface.

## Problem Statement

1) The global title “GEO GSM Curator UI” and the separate “GSE Identifier” section
   are redundant once a single GSE is active.

2) GSE-wide counts (Total GSMs, FLAGGED, Overrides, Outliers) are presented as a
   loose row rather than as a first-class grouped panel.

3) “Table controls” are separated from the curation table, forcing unnecessary
   vertical movement and breaking context.

## Proposed Change (UI Only)

### 1) Simplify Page Title and Remove GSE Identifier Section

- Remove the top-level page title “GEO GSM Curator UI”.
- Remove the entire “GSE Identifier” section.
- Use the active GSE accession (e.g. `GSE139566`) as the sole page title at the
  top of the page.

The sidebar remains the place for GSE selection.

### 2) Box GSE-Wide Counts as a Separate Panel

- Present GSE-wide counts in their own compact boxed panel, visually consistent
  with the “GSE-wide biology” panel.
- Panel label example:
  “GSE-wide counts (not affected by filters)”

Panel contents:
- Total GSMs
- FLAGGED (count and percent)
- Overrides
- Outliers

Do not repeat these metrics elsewhere on the page.

### 3) Merge Table Controls into the Curation Table Header

- Remove the standalone “Table controls” section entirely.
- Move the quick filter controls into the same horizontal row as the
  “Curation table” header.
- Align filters to the right side of the header.

Example:
  “Curation table        Quick filter: (All) (Needs attention) (Has overrides) (Clean)”

- Keep row count nearby (same panel), but do not introduce a separate section.

### Layout Rules

- The curation table should immediately follow its header.
- Avoid introducing new explanatory text.
- Maintain compact vertical spacing.

## Why No Backend Change Is Required

All changes are layout and presentation only. No data loading, filtering, or
semantics are altered.

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change

## Acceptance Criteria

1. The page title is the active GSE accession only.
2. The “GSE Identifier” section is fully removed.
3. GSE-wide counts appear in their own boxed panel, separate from biology.
4. Quick filter controls are inline with the “Curation table” header.
5. The page scrolls naturally from GSE context to curation work without
   redundant sections.

## Non-Goals

- No new metrics or summaries.
- No backend changes.
- No changes to filtering semantics.

## Constraints

- Preserve determinism and auditability.
- Keep the UI minimal and curator-focused.

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-116.md` and paste this ticket verbatim.
