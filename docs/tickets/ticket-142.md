# Ticket #142: Add `geo-gsm-summarize` to export GSM and GSE CSVs from an output directory (apply curator overrides)

## Background

After running the agent and completing curation in the UI, we need a CLI command that
summarizes an existing output directory into reporting-ready CSV files.

The UI already supports:
- exporting a per-GSM CSV of the 8 canonical fields
- exporting a per-GSE “biology summary” CSV
- applying saved curator overrides
- doing this without re-running backend processing

We want the same capability from the CLI for batch workflows on clusters.

## Problem Statement

There is no dedicated CLI command that:
1) scans an output directory containing one or more processed GSEs
2) loads final GSM annotations (8 canonical fields)
3) applies curator overrides produced by the UI
4) writes:
   - a GSM-level CSV (all GSMs, 8 fields)
   - a GSE-level CSV (one row per GSE, 7 fields; GSM accession removed)

Users currently must rely on UI export or manual scripts, which is not ideal for
batch automation.

## Proposed Change

Add a new subcommand:

```
geo-gsm-summarize --input-dir <DIR> [options]
```

This is a read-only summarization command:
- it must not call the LLM
- it must not re-run validation, repair, grounding, or decision logic
- it must only read existing output artifacts and curator overrides

### Inputs

Required:
- `--input-dir DIR`
  - directory containing outputs from one or more GSE runs
  - supports nested per-GSE output directories (current layout)

Optional:
- `--overrides PATH`
  - a path to overrides JSONL to apply (curator-produced)
  - if provided, it overrides any auto-detected overrides in the directory

- `--output-dir DIR`
  - where to write CSV files
  - default: `--input-dir`

- `--gsm-csv NAME`
  - default: `gsm_annotations.csv`

- `--gse-csv NAME`
  - default: `gse_summary.csv`

- `--strict`
  - if enabled, fail if expected artifacts are missing or unreadable
  - default behavior: warn and skip unreadable GSE subdirectories

### Artifact discovery rules

Within `--input-dir`, discover per-GSE output directories and locate the canonical
GSM annotation JSONL produced by the backend.

Implementation requirement:
- reuse the same artifact discovery and loader logic already used by the UI
  (to avoid divergence).
- do not guess new filenames if existing helpers exist.

### Override application

Apply overrides exactly as the UI does:
- use existing override parsing and application code (do not re-implement).
- overrides must be applied to the final GSM-level 8-field records before CSV export.
- precedence:
  1) `--overrides PATH` if provided
  2) otherwise, auto-detect saved overrides in the output directory using the same
     UI conventions
  3) otherwise, no overrides applied

### Outputs

1) GSM-level CSV
- One row per GSM.
- Exactly the 8 canonical fields, in this order:
  - `gse_accession`
  - `gsm_accession`
  - `data_type`
  - `organism`
  - `tissue_type`
  - `cell_line`
  - `disease`
  - `treatment`

2) GSE-level CSV
- One row per GSE.
- Exactly 7 fields (GSM accession removed), in this order:
  - `gse_accession`
  - `data_type`
  - `organism`
  - `tissue_type`
  - `cell_line`
  - `disease`
  - `treatment`

GSE-level value derivation requirement:
- reuse the existing “GSE-wide biology summary” logic already implemented for the UI.
- do not introduce new summarization semantics in this ticket.

### Runtime messages

Print concise progress messages (stderr/logger), for example:
- `INFO: summarize: scanning <input-dir>`
- `INFO: summarize: loaded N GSM records across M GSEs`
- `INFO: summarize: applied overrides from <path>` (or `none`)
- `INFO: summarize: wrote <gsm_csv_path>`
- `INFO: summarize: wrote <gse_csv_path>`

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change (policy-spec.md must be updated)

This ticket introduces export convenience only. It must not change backend semantics.

## Acceptance Criteria

1. `geo-gsm-summarize --help` documents all options clearly.
2. Running `geo-gsm-summarize`:
   - does not invoke the LLM
   - does not re-run backend processing
3. GSM CSV contains all GSMs found under `--input-dir`, with exactly 8 columns
   in the canonical order.
4. GSE CSV contains one row per GSE, with exactly 7 columns (no gsm_accession),
   using the same GSE summary logic as the UI.
5. Overrides are applied with correct precedence and match UI export results.
6. Missing/unreadable GSE directories:
   - default: warn and skip
   - with `--strict`: fail fast with clear error
7. Add tests:
   - create a small synthetic output directory with known GSM JSONL
   - include an overrides JSONL and verify overridden values appear in both CSVs
   - verify column order and row counts
8. `uv run pytest -q` passes.

## Non-Goals

- No changes to validation, repair, ontology, or decision logic.
- No new summary heuristics or cross-GSM inference beyond what UI already does.
- No UI changes.

## Constraints

- Export must be deterministic and reproducible.
- Use shared code paths with UI loaders/exports to avoid drift.
- Output schema must remain exactly the canonical fields.

## Guiding Principle

Exports must reflect existing outputs plus explicit curator overrides, with no reprocessing.

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-142.md` and paste this ticket verbatim.
