# Ticket #192: Add a read-only output statistics script for ARTNet run directories

## Background

We have full-run output under `out/artnet`, with one subdirectory per GSE. Each per-GSE
directory already contains authoritative backend artifacts such as:

- `audit.jsonl`
- `curation.jsonl`
- `evidence.jsonl`
- `flagged.jsonl`
- `suggestions.jsonl`
- `gse_consistency.json`

For analysis and reporting, we need a dedicated script that summarizes these existing
artifacts across the whole ARTNet run without re-running the pipeline.

The immediate questions include:

- how many GSMs ended `FLAGGED`
- how many GSMs went through repair activity
- how many values were normalized through ontology grounding
- how many total LLM calls occurred, including proposal and repair calls

The whitepaper and policy documents also make additional read-only summary metrics useful,
including final decision totals, terminal fallbacks, flags, primary failures, ontology
status distributions, and GSE-level advisory suggestion counts.

## Problem Statement

There is currently no dedicated, version-controlled utility for computing run-wide summary
statistics from existing output artifacts.

Users must manually inspect many per-GSE directories or write ad hoc one-off commands,
which is error-prone and not auditable.

## Proposed Change

Add a standalone script under a dedicated `scripts/` directory that scans a run output
directory such as `out/artnet` and produces aggregate statistics from existing artifacts only.

Proposed script behavior:

1. Accept an input directory containing `GSE*` subdirectories.
2. Read authoritative backend artifacts, with `audit.jsonl` as the primary source for
   run-level execution, repair, grounding, and decision metrics.
3. Use `evidence.jsonl` for per-field diagnostic flag counts.
4. Use `suggestions.jsonl` for GSE-level advisory outlier suggestion counts.
5. Report totals including, at minimum:
   - number of GSE directories processed
   - number of GSM records processed
   - final decision counts
   - number of flagged GSMs
   - total LLM calls
   - proposal-call count vs repair-call count
   - GSMs with any repair activity
   - GSMs with LLM repair attempts
   - GSMs with deterministic fallback actions
   - ontology canonicalization counts
   - changed-value ontology canonicalization counts
   - terminal fallback counts
   - top flags and primary failures
   - ontology status counts by field
   - field-level diagnostic flag counts
   - GSE advisory suggestion counts
6. Support both a human-readable text summary and a machine-readable JSON summary.
7. Remain strictly read-only:
   - no LLM calls
   - no validation reruns
   - no ontology reruns
   - no output schema changes
   - no modification of any run artifacts

## Layer Affected

- [ ] Canonicalization
- [ ] Ontology grounding
- [ ] Validation / Repair
- [ ] Decision routing
- [ ] UI only
- [ ] Documentation only

Reporting / read-only utility only.

## Policy Impact

- [x] No policy change
- [ ] Policy clarification only
- [ ] Policy change (policy-spec.md must be updated)

This ticket adds analysis over existing artifacts only. It must not change backend
semantics, schema, or audit behavior.

## Acceptance Criteria

1. A script exists under `scripts/` for aggregating output statistics from a run directory.
2. The script reads existing artifacts only and does not invoke LLMs or rerun backend logic.
3. The script reports the requested totals for:
   - flagged GSMs
   - repair activity
   - ontology-driven normalization
   - total LLM calls
4. The script also reports additional audit-oriented metrics derived from authoritative
   artifacts, including flags, primary failures, terminal fallbacks, ontology statuses,
   and GSE suggestion counts.
5. The script can emit a JSON summary suitable for downstream analysis.
6. Add a focused automated test covering aggregation on a small synthetic output tree.
7. `uv run pytest -q` passes.

## Non-Goals

- Any backend behavior change.
- Any change to JSONL schemas or the canonical 8-field output contract.
- Any reprocessing of GSMs, re-grounding, or revalidation.
- Any UI changes.

## Constraints

- Use existing artifacts as ground truth.
- Prefer `audit.jsonl` for execution and decision statistics.
- Treat `evidence.jsonl` as authoritative for per-field diagnostics.
- Keep the utility deterministic and read-only.
- Do not silently reinterpret backend semantics.

## Guiding Principle

Summaries must reflect already-emitted backend artifacts exactly, with no inference and no
pipeline side effects.

## Ticket File Requirement (MANDATORY)

Create `docs/tickets/ticket-192.md` and paste this ticket verbatim.
