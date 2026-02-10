# Ticket #144: Sticky accession columns in curation table

## Background

During horizontal scrolling in the curation table, the identity columns (`gse_accession`, `gsm_accession`) can scroll out of view. This increases curator error risk when editing right-side fields (e.g., `disease`, `treatment`) because row identity is no longer visible.

## Problem Statement

The table allows horizontal scrolling across many columns, but row identity is not preserved in view. Curators can lose track of which GSM they are editing, especially during multi-row selection and bulk edits.

## Proposed Change

In the curation table UI:

- Pin (sticky) the leftmost identity columns so they remain visible during horizontal scrolling:
  - `gse_accession`
  - `gsm_accession`
- Keep the row selection checkbox column visible as well (sticky).
- Maintain existing column ordering and sorting behavior.
- No changes to data loading, filtering semantics, or export behavior.

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change (policy-spec.md must be updated)

## Acceptance Criteria

- When horizontally scrolling the table, `gse_accession` and `gsm_accession` remain visible at all times.
- Sticky columns do not break:
  - row selection
  - hover diagnostics/tooltips
  - edit controls
  - bulk edit selection behavior
- Table layout remains stable on common screen widths (no overlapping text or unusable clipping).

## Non-Goals

- No changes to backend artifacts, schema, or audit behavior.
- No changes to what values are editable or how edits are validated (UI-side safety remains as-is).
- No new filtering logic.

## Constraints

- UI must remain a read-only consumer of `curation.jsonl`, `audit.jsonl`, and `evidence.jsonl`.
- No re-running validation, repair, ontology grounding, or decision routing.
- Preserve deterministic display behavior (no hidden resorting or implicit grouping).

## Guiding Principle

**UI improves ergonomics without changing meaning.**  
Sticky columns reduce curator mistakes without altering backend semantics.

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-144.md` and paste this ticket verbatim.
