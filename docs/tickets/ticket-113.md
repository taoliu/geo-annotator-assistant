# Ticket #113: Top-of-Page Declutter + True GSE-Level Summary from gse_field_values.jsonl

## Background

After recent UI enhancements (multi-GSE loading, collapsible sections, triage),
the top-of-page area still contains redundant headings and repeated summary
metrics. This reduces scanability and wastes vertical space.

Additionally, curators want to see GSE-wide summary metadata (field consensus)
from `gse_field_values.jsonl`, clearly labeled as applying to the whole GSE and
not dependent on current filters.

## Problem Statement

1) The header “Active GSE: GSE174635” is verbose and redundant.

2) The UI currently shows summary metrics that reflect current filters, but does
not surface the GSE-wide summary fields available in `gse_field_values.jsonl`.

3) There are two summary blocks with overlapping metrics:
- “Total GSMs / Needs attention / Has overrides / Clean”
- “GSE Summary: Total GSMs / FLAGGED / Overrides / Outliers”
This repeats “Total GSMs” and “Overrides/Has overrides” and is not necessary.

4) “Quick filter (single choice)” uses extra vertical space; the label and
options can be compacted into one row.

## Proposed Change (UI Only)

### 1) Simplify Active GSE Heading

Replace:
- “Active GSE: GSE174635”
with:
- “GSE174635”

(Keep the GSE selector in the sidebar as the true source of active selection.)

### 2) Add GSE-Wide Summary from gse_field_values.jsonl

Inputs:
- Add optional loading of `gse_field_values.jsonl` from each GSE directory.

Behavior:
- If `gse_field_values.jsonl` exists for the active GSE, show a compact
  “GSE-wide summary” panel near the top.
- This panel must be explicitly labeled:
  - “GSE-wide (not affected by filters)”
- It should display the summary field values (as present in the file) in a clean
  compact layout, for example:
  - data_type
  - organism
  - tissue_type
  - cell_line
  - disease
  - treatment
  (exact fields displayed should match the file content; do not invent fields)

- If the file is absent, the UI should omit this panel (no error).

### 3) Merge / Remove Redundant Metric Blocks

Consolidate top-level metrics into a single compact metric row (or single panel)
that avoids duplicates.

Keep only these metrics (GSE-wide, not filter-dependent):
- Total GSMs
- FLAGGED (count and percent)
- Overrides (count of GSMs with overrides saved/loaded for this GSE, plus
  optionally session-only unsaved count)
- Outliers (count)

Remove the redundant block that separately shows:
- “Needs attention”
- “Has overrides”
- “Clean”
and any duplicated “Total GSMs” / “Overrides”.

Notes:
- If “Clean” is still useful, it can be derived as:
  Total - FLAGGED - Overrides (if that matches your existing definition),
  but do not add new semantics. Prefer to omit it rather than invent.

Filter-dependent messaging:
- If the UI still presents a filtered view, keep a small, subtle note near the
  table such as:
  “Table reflects current filters.”
- Do not mix filter-dependent counts into the GSE-wide metric row.

### 4) Compact the Quick Filter Row

Make the “Quick filter (single choice)” label and its options appear on a single
row of text, e.g.

“Quick filter: [All] [Needs attention] [Has overrides] [Clean]”

Implementation notes:
- Keep the same filter semantics as current UI.
- If Streamlit radio buttons cannot be laid out as desired, use an alternative
  UI control that maintains single-choice behavior.

## Why No Backend Change Is Required

- `gse_field_values.jsonl` is a read-only input artifact.
- All changes are layout and presentation.
- No validation/repair logic or schemas are modified.

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change

## Acceptance Criteria

1. The page header shows only the GSE accession (e.g. “GSE174635”).
2. If `gse_field_values.jsonl` is present, a “GSE-wide summary (not affected by
   filters)” panel is shown with the file’s field values.
3. Redundant metric sections are merged into a single non-duplicative metric row
   (Total GSMs, FLAGGED, Overrides, Outliers).
4. The “Quick filter” label and options are displayed in one compact row without
   changing filter semantics.
5. UI remains read-only (except explicit override save/export actions).

## Non-Goals

- No new summary computations beyond displaying what exists in
  `gse_field_values.jsonl`.
- No changes to filtering logic semantics.
- No backend changes.

## Constraints

- Do not mix GSE-wide counts with filter-dependent counts in the same metric row.
- The GSE-wide panel must explicitly state it ignores filters.
- Maintain performance in multi-GSE mode.

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-113.md` and paste this ticket verbatim.
