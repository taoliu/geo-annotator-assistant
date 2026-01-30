# Ticket #107: Support Multi-GSE Loading from a Parent Directory (Scan GSE* Subdirectories) + GSE Switcher

## Background

Curators often want to review many GSE runs in one UI session. Today the UI is
typically launched for a single GSE directory, e.g.

uv run python -m ui.cli --input-dir out/test_ui/GSE154879

But the common workflow is to point the UI at a parent directory such as
out/test_ui/ that contains many GSE* subdirectories.

## Problem Statement

The current UI does not support loading multiple GSEs at once, which forces
curators to restart the UI for each GSE. This is slow and interrupts workflow.

## Proposed Change (UI Only)

### 1) Directory Scanning Mode (Formal Launch Path)

When `--input-dir` is a directory that contains subdirectories matching `GSE*`,
treat it as a multi-GSE root:

- scan `--input-dir` for immediate children with names matching `GSE*`
  (directory only)
- for each `GSE*` directory, attempt to load:
  - `curation.jsonl`
  - `evidence.jsonl`
  - `suggestions.jsonl` (optional)
  - `audit.jsonl` (optional, per Ticket #106)

If `--input-dir` directly contains `curation.jsonl`, treat it as the existing
single-GSE mode (backward compatible).

### 2) GSE Switcher

Add a simple UI control to select the active GSE from the loaded set:
- dropdown (or sidebar list) of loaded GSE accessions
- display active GSE name prominently above the GSM table
- switching GSE updates the GSM table and modal data source

### 3) Error Handling / UX

- If a candidate `GSE*` directory is missing required files, exclude it from
  the list and show a small warning panel summarizing skipped directories and
  reasons (read-only).
- Do not crash the UI due to one bad directory.

### 4) Documentation Update

Update `docs/ui.md` to document:
- launching with a multi-GSE root directory
- the `GSE*` scanning behavior
- how the UI indicates skipped datasets

## Why No Backend Change Is Required

This only changes UI loaders and navigation. It consumes existing output
artifacts without altering schemas or backend behavior.

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change

## Acceptance Criteria

1. Launching with `--input-dir out/test_ui/` loads all valid `GSE*` children and
   presents a GSE switcher.
2. Launching with `--input-dir out/test_ui/GSE154879` continues to work.
3. Switching the active GSE updates the GSM table and modal correctly.
4. Skipped GSE directories are reported in a clear, read-only summary panel.
5. No files are modified unless explicitly exporting overrides (existing behavior).
6. `docs/ui.md` is updated accordingly.

## Non-Goals

- No cross-GSE aggregation or inference.
- No backend reprocessing.

## Constraints

- Must remain read-only with respect to backend semantics.
- Keep load time reasonable; prefer lazy-loading per GSE if needed.

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-107.md` and paste this ticket verbatim.
