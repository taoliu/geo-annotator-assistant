# Ticket #132: Export all final annotations across loaded input-dir as a single CSV (UI-only)

## Background

The curator UI can be launched with:

`uv run python -m ui.cli --input-dir <DIR>`

In this mode, the UI loads multiple GSE folders/records under the input directory and
allows switching among them in a single session.

Curators need a single “all results” CSV for reporting, spanning all loaded GSMs across
all GSEs, with overrides applied.

## Problem Statement

Currently, export is scoped to the active GSE (JSONL and/or CSV). Curators must export
per-GSE and then manually merge files for reports. This is slow and error-prone.

## Proposed Change

Add a left-side (sidebar) export control:

### A) New export action
- Add a button labeled: **Export ALL final annotations as CSV**
- Place it in the left sidebar near the input-dir / GSE selection controls.

### B) Export content and semantics
The exported CSV must contain one row per GSM across **all loaded GSEs** under the
input-dir, and include exactly the 8 canonical output fields:

- `gse_accession`
- `gsm_accession`
- `data_type`
- `organism`
- `tissue_type`
- `cell_line`
- `disease`
- `treatment`

Values must be the “final annotations” as currently defined by the UI:
- backend annotation values (from existing artifacts)
- with explicit saved overrides applied (same semantics as per-GSE export)

This export must not trigger backend re-runs, re-validation, or re-grounding.

### C) Source of data (read-only)
For each loaded GSE under input-dir:
- Load the same per-GSE “final annotation” records used by the existing export.
- Apply saved overrides for that GSE (if present), using the same override application logic.

Combine all GSM rows into a single dataframe and export as CSV.

### D) Deterministic output naming
- Filename should be deterministic and tied to the input directory name, e.g.:
  - `final_annotations_ALL.csv`
  - or `<input_dir_basename>_final_annotations.csv`

### E) Sorting (deterministic)
Sort rows deterministically, for example:
1) `gse_accession` ascending
2) `gsm_accession` ascending

### F) Safety and transparency
- If a GSE is missing required artifacts, skip it and show a UI warning listing skipped
  GSEs (UI-only).
- Do not silently drop GSMs without notifying the curator.

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change (policy-spec.md must be updated)

## Acceptance Criteria

- A sidebar button exists to export all final annotations across input-dir as one CSV.
- The CSV contains exactly the 8 canonical columns listed above.
- Overrides are applied identically to existing per-GSE export semantics.
- Export does not depend on which GSE is currently selected.
- Export is deterministic (stable sorting + stable filename).
- No backend artifacts are modified.

## Non-Goals

- Do not add extra diagnostic columns (flags, evidence, etc.).
- Do not merge or infer across GSMs.
- Do not export unsaved session-only edits (unless already included by current “final export” semantics).
  This export must match saved override semantics.

## Constraints

- UI-only change.
- Must scale reasonably to large input-dir datasets without recomputing heavy artifacts.

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-132.md` and paste this ticket verbatim.
