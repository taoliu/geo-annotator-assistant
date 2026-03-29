# Ticket #196: Skip no-sample GSE SOFT files regardless of source path

## Background

Ticket #194 introduced deterministic skipping for GSE SOFT files that legitimately
contain no `SAMPLE` / GSM records, but only in the local-first mirror path.

The underlying condition is not specific to local mirrors. A valid SOFT file with zero
sample records remains non-actionable whether it comes from:

- a local repository mirror
- a cache hit
- a fresh remote download
- an explicit `--gse-soft` file path

## Problem Statement

Current behavior is inconsistent across ingest paths:

- local-first mirror mode skips no-sample SOFT files
- remote-only accession mode still raises
- explicit SOFT-file mode still raises

This makes terminal behavior depend on file origin rather than the authoritative
content of the SOFT file.

## Proposed Change

Generalize no-sample handling so that a GSE SOFT file with zero `SAMPLE` / GSM entries
is treated as a terminal skip condition across all GSE ingest modes.

Behavior change:

1. When parsing determines that a SOFT file contains no sample data:
   - do not retry or re-download because of that condition alone
   - emit a clear warning
   - skip the GSE deterministically

2. Apply the same skip semantics to:
   - local-first mirror ingest
   - cached / remote-only accession ingest
   - explicit `--gse-soft` file ingest

3. Preserve existing bounded retry behavior for true parser/read failures.

4. CLI handling must treat the generalized no-sample skip as non-fatal for all GSE
   input modes.

## Layer Affected

- [ ] Canonicalization
- [ ] Ontology grounding
- [ ] Validation / Repair
- [ ] Decision routing
- [ ] UI only
- [ ] Documentation only

Ingest / SOFT loading only.

## Policy Impact

- [x] No policy change
- [ ] Policy clarification only
- [ ] Policy change (policy-spec.md must be updated)

This ticket changes ingest termination behavior only. It must not alter annotation
semantics, pipeline order, schema, or audit behavior for processed GSMs.

## Acceptance Criteria

1. A no-sample SOFT file skips in local-first mirror mode.
2. A no-sample SOFT file skips in remote-only accession mode, including cache-backed
   and freshly downloaded cases.
3. A no-sample SOFT file skips in explicit `--gse-soft` mode.
4. CLI handling treats these skips as non-fatal and continues or exits cleanly,
   depending on single-file vs batch mode.
5. True parser/read failures still follow existing retry/error behavior.
6. `uv run pytest -q` passes.

## Non-Goals

- Changing GEOparse extraction semantics beyond recognizing the zero-sample terminal
  condition.
- Changing missing-file policy semantics.
- Changing backend annotation policy.

## Constraints

- Keep retry bounded to transport/read failures only.
- Do not reinterpret zero-sample SOFT files as corruption.
- Preserve compatibility for existing local-mirror skip behavior.

## Guiding Principle

Terminal ingest outcomes should be determined by SOFT content, not by where the SOFT
file came from.

## Ticket File Requirement (MANDATORY)

Create `docs/tickets/ticket-196.md` and paste this ticket verbatim.
