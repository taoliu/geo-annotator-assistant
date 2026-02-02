# Ticket #112: GEO Accession Hyperlinks in Table + Column-Level Flag Highlighting

## Background

Curators often need to jump from the UI to the corresponding GEO landing pages
for a GSE or GSM. Today, accessions are plain text.

Also, even when a GSM is FLAGGED, curators still need to visually locate which
field(s) are implicated. The table currently highlights status at the row level
but not at the cell level for the core biology columns.

## Problem Statement

1) `gse_accession` and `gsm_accession` cells are not clickable, forcing manual
   copy/paste into NCBI GEO.

2) The table does not visually indicate which specific field(s) in
   `data_type`, `organism`, `tissue_type`, `cell_line`, or `disease` are flagged
   for a given GSM. This slows triage and increases modal open frequency.

## Proposed Change (UI Only)

### 1) Hyperlink Accessions to NCBI GEO

Render `gse_accession` and `gsm_accession` values as hyperlinks:

- For a GSE accession `GSE174635`:
  `https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE174635`
- For a GSM accession `GSM5320850`:
  `https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSM5320850`

Behavior:
- Clicking the accession opens the GEO page in a new browser tab (preferred) or
  navigates in the same tab if that is the only supported option.
- This click target must not interfere with the existing “open modal” behavior
  (decision icon click remains the primary modal open action).

Implementation notes:
- Use a safe rendering method (e.g., Streamlit markdown/HTML rendering with
  escaping) to avoid injection risks.
- Do not write raw URLs into JSONL; links are UI-rendered only.

### 2) Column-Level Flag Highlighting for Core Fields

For each table row, apply a visual highlight (e.g., red background tint or red
left-border) to the specific core field cells if that field is flagged.

Target columns:
- `data_type`
- `organism`
- `tissue_type`
- `cell_line`
- `disease`

Source of truth:
- `evidence.jsonl.evidence_by_field[<field>].flags`
  and/or row-level `curation.jsonl.flags` when they encode field association.

Rules:
- If `evidence_by_field[field].flags` is non-empty, highlight that cell.
- If evidence is missing, do not infer highlights.
- Do not highlight `treatment` by default unless it is explicitly flagged and
  the UI already surfaces treatment identity flags (optional extension).

Presentation:
- Highlight must be subtle enough to keep table readable.
- Include a tooltip on the highlighted cell showing the relevant flag(s)
  (short labels only; detailed explanation remains in the modal).

### Guardrails

- No new inference: highlighting is purely based on existing per-field evidence.
- No changes to backend logic or schemas.
- Ensure table performance remains acceptable for large datasets.

## Why No Backend Change Is Required

- GEO links are deterministically constructed from accessions already in
  `curation.jsonl`.
- Per-field flags already exist in `evidence.jsonl` for UI consumption.

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change

## Acceptance Criteria

1. `gse_accession` and `gsm_accession` render as clickable links to NCBI GEO.
2. Clicking an accession does not break the “open modal” interaction
   (decision icon click still opens modal).
3. Cells in core columns are visually highlighted when their corresponding
   `evidence_by_field[field].flags` is non-empty.
4. Highlighted cells show a tooltip listing the flag(s) for that field.
5. No JSONL files are modified.

## Non-Goals

- No automatic diagnosis of which field is wrong.
- No new flag generation or reclassification.
- No backend changes.

## Constraints

- Use safe rendering for links.
- Preserve determinism and auditability.
- Keep UI responsive for large tables.

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-112.md` and paste this ticket verbatim.
