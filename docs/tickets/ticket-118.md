# Ticket #118: Export final annotations as CSV

## Background

The UI can export final annotations as `annotation.jsonl` (8-field output with overrides applied),
but curators often need a CSV for reports and spreadsheets.

## Problem Statement

Curators must manually convert JSONL to CSV outside the tool, which is extra work and error-prone.

## Proposed Change

Add a new button near the existing “Export final annotations” control:

- Label: **Export final annotations as CSV**

The CSV must contain one row per GSM and include exactly the 8 canonical output fields
(header included), in this order:

- `gse_accession`
- `gsm_accession`
- `data_type`
- `organism`
- `tissue_type`
- `cell_line`
- `disease`
- `treatment`

Data source must be the **same final-annotation assembly currently used for JSONL export**:
backend outputs with **explicit overrides applied**, with no re-validation or re-inference.

The download filename should be deterministic, e.g.:
`<GSE>_final_annotations.csv`

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change (policy-spec.md must be updated)

## Acceptance Criteria

- A new CSV export button exists near the JSONL export button.
- Clicking it downloads a CSV with:
  - header row
  - one row per GSM
  - exactly 8 columns in the specified order
- Values match the JSONL export content (same overrides applied, same final values).
- No backend artifacts are modified or regenerated.

## Non-Goals

- Do not add extra “helper” columns (flags, failure codes, matched ontology IDs, etc.).
- Do not change JSONL export behavior or its schema.
- No bulk override logic and no UI inference.

## Constraints

- UI-only change. Backend behavior is frozen.
- Exported CSV is a derived convenience artifact for reporting.

## Guiding Principle

Backend output is the source of truth; the UI only formats and exports it.

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-118.md` and paste this ticket verbatim.
