# Ticket #117: Export GSE-wide biology panel as CSV

## Background

Curators use the “GSE-wide Biology (Not affected by filters)” panel as a concise summary
for reports, but currently must manually copy values.

## Problem Statement

There is no one-click export for the GSE-wide biology summary. This adds manual work
and creates risk of transcription mistakes.

## Proposed Change

Add an **Export CSV** button at the top of the “GSE-wide Biology (Not affected by filters)”
panel.

The CSV must contain exactly one row with these columns (header included):

- `gse_accession`
- `data_type`
- `organism`
- `tissue_type`
- `cell_line`
- `disease`

Data source is the **same UI-derived GSE-wide biology summary currently displayed**
(not affected by table filters).

The download filename should be deterministic, e.g.:
`<GSE>_gse_wide_biology.csv`

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change (policy-spec.md must be updated)

## Acceptance Criteria

- A visible button exists at the top of the GSE-wide biology panel.
- Clicking it downloads a CSV with one row and the exact columns listed above.
- Values match what is displayed in the GSE-wide biology panel.
- Export is not affected by table filters.
- No backend artifacts are modified or regenerated.

## Non-Goals

- No new inference, aggregation rules, or “majority vote” logic.
- No additional columns beyond those listed.
- No changes to backend schema or JSONL exports.

## Constraints

- UI-only change. Backend output remains the source of truth.
- Exported CSV is a derived convenience artifact.
- Prefer deterministic filenames and stable column ordering.

## Guiding Principle

UI reflects state, it does not infer or fix.

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-117.md` and paste this ticket verbatim.
