# Ticket #123: Drive essential-column cell highlighting from evidence.jsonl per-field flags

## Background

Curator scanning depends on consistent cell-level highlighting for the five essential
biology fields. In the AG Grid table, highlighting was attempted using summary fields
(e.g., `flagged_fields`), but this is not the correct source of truth for per-field UI signals.

The authoritative per-field signal is in `evidence.jsonl`:

`evidence_by_field.<field>.flags`

Example:
`tissue_type.flags = ["ontology_low_confidence_tissue_type"]` should highlight the
`tissue_type` cell for that GSM.

## Problem Statement

The AG Grid table does not highlight essential biology cells based on the true per-field
evidence flags, causing a mismatch between what the evidence artifact reports and what
the curator sees in the table.

## Proposed Change

Update the UI table row model to attach per-field evidence flags from `evidence.jsonl`,
and use them to drive cell-level highlighting for the five essential columns.

### Data sourcing (read-only)
- Load `evidence.jsonl` for the active GSE (already an expected artifact).
- Build a lookup keyed by `gsm_accession`.
- For each GSM row, attach (at minimum) these UI-only helper fields:
  - `evidence_flags_data_type`
  - `evidence_flags_organism`
  - `evidence_flags_tissue_type`
  - `evidence_flags_cell_line`
  - `evidence_flags_disease`

Each helper field is a list of strings (flags), defaulting to an empty list.

### Highlight rule
For each essential column cell:
- Apply the “flagged” background highlight iff the corresponding evidence flags list
  is non-empty.

This must be independent of `primary_failure`, `flag_summary`, or `flagged_fields`.

### Constraints
- No new inference and no recomputation of backend decisions.
- Evidence is displayed only; backend remains authoritative.
- Keep existing coloring for non-essential diagnostic columns unchanged unless it
  conflicts.

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change (policy-spec.md must be updated)

## Acceptance Criteria

- If `evidence_by_field.tissue_type.flags` is non-empty for a GSM, the `tissue_type`
  cell is highlighted in the table.
- Same rule applies for `data_type`, `organism`, `cell_line`, `disease`.
- GSMs with empty flags for a field do not highlight that field’s cell.
- Highlighting persists across reruns and filtering.
- No backend actions are triggered.

## Non-Goals

- Do not invent new flags.
- Do not highlight based on ontology_status alone unless it is already represented as a flag.
- Do not change backend artifact generation.

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-123.md` and paste this ticket verbatim.
