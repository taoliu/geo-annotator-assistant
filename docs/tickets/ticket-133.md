# Ticket #133: Add `--gse-file` to support processing multiple GSE accessions

## Background

Current CLI supports exactly one GSE via `--gse` (or a local SOFT via `--gse-soft`), plus GSM-centric inputs (`--gsm`, `--gsm-file`) and `--jsonl`. The curator workflow increasingly needs batch runs over multiple GSEs listed in a plain text file (one GSE per line).

## Problem Statement

There is no supported way to pass a list of GSE accessions to `geo-gsm-annotate` in a single invocation while preserving explicit, non-implicit batch semantics.

## Proposed Change

Add a new mutually-exclusive input option:

- `--gse-file PATH` : plain text file, one GSE accession per line.
  - Trim whitespace.
  - Ignore blank lines.
  - Ignore lines starting with `#` (comment lines).
  - Deduplicate while preserving first-seen order.

Execution semantics:
- For each GSE in the resolved list, run the existing single-GSE pipeline exactly as `--gse` would.
- Output layout must be deterministic and auditable:
  - If `--output-dir OUT` is provided, write per-GSE outputs under:
    - `OUT/<GSE>/` (one directory per GSE)
  - If `--output-dir` is not provided, keep existing default behavior for single-GSE, and for `--gse-file` choose a deterministic batch default:
    - `./outputs/<RUN_STAMP>/` or `./outputs/` with a deterministic subdir name (see Acceptance Criteria).
  - Do not merge GSE outputs into a single JSONL file unless an explicit *new* flag is introduced in a later ticket.

CLI help text updates:
- Update usage line to include `--gse-file`.
- Document that `--gse-file` is batch and is never inferred.

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change (policy-spec.md must be updated)

This ticket changes only CLI input handling and output directory routing. It must not alter pipeline stage order, validators, repair loops, ontology grounding, or decision logic.

## Acceptance Criteria

1. `uv run geo-gsm-annotate -h` lists `--gse-file` with clear help text.
2. `--gse-file` is mutually exclusive with `--gsm`, `--gsm-file`, `--jsonl`, `--gse`, `--gse-soft`.
3. Given a file with GSEs + blank lines + comments, the resolved list matches the intended rules (trim, ignore blanks/comments, stable dedupe).
4. Running with `--gse-file` produces per-GSE output directories under `--output-dir/<GSE>/`.
5. Existing single-GSE and single-GSM behaviors are unchanged.
6. Add/extend unit tests (likely in `tests/test_cli_and_batch.py`) covering parsing rules and output directory layout.

## Non-Goals

- No backend semantic changes.
- No changes to report content, JSONL schemas, or field-level outputs.
- No UI changes.
- No automatic parallelism.

## Constraints

- Batch operations must never be implicit.
- Output paths must be deterministic and auditable.
- Preserve the 8-field output contract.

## Guiding Principle

CLI ergonomics must not obscure semantics.

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-133.md` and paste this ticket verbatim.
