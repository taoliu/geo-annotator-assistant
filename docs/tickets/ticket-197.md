# Ticket #197: Add resumable `--gse-file` mode that skips GSEs with complete existing outputs

## Background

`geo-gsm-annotate --gse-file` is used for long-running multi-GSE batch jobs. If the
process is interrupted, rerunning the batch currently starts from the top and
reprocesses GSEs that already finished successfully.

The batch output structure is already deterministic:

- batch base directory
- per-GSE subdirectory under `<output-dir>/<GSE>/`
- stable artifact filenames written by `write_run_outputs()`

This makes output-directory-based resume feasible without altering backend semantics.

## Problem Statement

There is currently no CLI option to skip GSEs that were already processed in a prior
batch run. As a result, resuming after an accidental interrupt wastes time and compute.

## Proposed Change

Add a batch-only CLI option that enables resumable `--gse-file` execution by checking
the per-GSE output directory before processing each accession.

### New CLI option

- Add `--resume`
- Intended for `--gse-file` runs

### Resume semantics

For each GSE in a `--gse-file` batch:

1. Resolve the expected per-GSE output directory deterministically as currently done.
2. If `--resume` is enabled and that directory already contains a complete set of core
   output artifacts from a prior successful run, skip the GSE.
3. If the directory is missing or only partially populated, process the GSE normally.

### Completeness rule

A GSE counts as already processed only if its output directory contains the full core
artifact set written by `write_run_outputs()`:

- `annotations.jsonl`
- `audit.jsonl`
- `flagged.jsonl`
- `curation.tsv`
- `curation.jsonl`
- `evidence.jsonl`

If `--emit-suggestions` is enabled for the current run, also require:

- `suggestions.jsonl`

This avoids falsely skipping GSEs after partially written outputs from an interrupted
run.

### Messaging

Emit an informational stderr message when a GSE is skipped due to `--resume`.

## Layer Affected

- [ ] Canonicalization
- [ ] Ontology grounding
- [ ] Validation / Repair
- [ ] Decision routing
- [ ] UI only
- [ ] Documentation only

CLI orchestration / output resumption only.

## Policy Impact

- [x] No policy change
- [ ] Policy clarification only
- [ ] Policy change (policy-spec.md must be updated)

This ticket changes batch orchestration only. It must not alter annotation semantics,
pipeline ordering within a processed GSE, schema, or audit content.

## Acceptance Criteria

1. `uv run geo-gsm-annotate --gse-file ... --resume` skips GSEs with complete existing
   output directories.
2. Incomplete per-GSE output directories are not skipped.
3. Resume detection uses deterministic per-GSE output paths.
4. An informational skip message is emitted for resumed GSEs.
5. Tests cover:
   - complete output directory causes skip
   - partial output directory does not skip
6. `uv run pytest -q` passes.

## Non-Goals

- Merging or reconciling partially written outputs.
- Inferring completion from audit content rather than file presence.
- Changing single-GSE or non-GSE batch modes.

## Constraints

- Keep resume behavior opt-in.
- Do not silently skip based on directory existence alone.
- Use current output artifact names as the source of truth for completion.

## Guiding Principle

Resuming a long batch should be safe by default: skip only when prior completion is
clear from the full expected output artifact set.

## Ticket File Requirement (MANDATORY)

Create `docs/tickets/ticket-197.md` and paste this ticket verbatim.
