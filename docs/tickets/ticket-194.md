# Ticket #194: Skip local SOFT files that legitimately contain no SAMPLE data

## Background

Some GEO family SOFT files are valid series records but contain no `SAMPLE` / GSM
sections. In local-first ingest mode, these files are currently treated the same as
corrupted or unparsable local SOFT files.

That behavior is a poor fit for restricted environments where remote download is not
available or is intentionally disabled in practice. A real no-sample series should be
recognized as non-actionable and skipped, not re-downloaded.

## Problem Statement

The current local-first retry logic in `soft_to_context_jsonl()` treats
`"No sample data extracted from <path>"` as a generic local parse failure and, when
`geo_soft_on_missing=remote`, attempts a re-download.

This causes unnecessary retry stalls for valid no-sample series such as `GSE292080`,
even though re-downloading cannot create missing GSM records that do not exist in the
source data.

## Proposed Change

Refine local-first SOFT ingest so that "no sample data extracted" is classified
separately from true parser/read failures.

Behavior change:

1. When a local SOFT file exists and parsing determines that the series contains zero
   GSM / `SAMPLE` entries:
   - do not re-download
   - emit a warning that the SOFT contains no sample data
   - skip the GSE deterministically

2. When a local SOFT file fails to read or parse for other reasons (corruption,
   truncated gzip, parser exception, etc.):
   - preserve the existing Ticket #141 retry-on-parse-failure behavior

3. If a local miss triggers a download and the downloaded SOFT still contains no sample
   data:
   - skip without any additional retry loop

4. Batch CLI handling must continue past skipped GSEs and print an accurate skip
   message for the no-sample case.

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

This ticket changes ingest robustness only. It must not alter annotation semantics,
pipeline order, output schema, or audit semantics for accepted GSM records.

## Acceptance Criteria

1. Local-first mode does not re-download when the local SOFT exists and contains no
   sample data.
2. The no-sample case is skipped with a clear warning instead of aborting the batch.
3. True parser/read failures still trigger the existing single re-download retry.
4. If a downloaded replacement SOFT contains no sample data, the run skips without a
   second retry loop.
5. Automated tests cover:
   - local existing file with no sample data skips without download
   - CLI batch processing continues when a GSE is skipped for no sample data
6. `uv run pytest -q` passes.

## Non-Goals

- Changing GEOparse extraction semantics beyond distinguishing no-sample versus parse
  failure.
- Changing remote-only ingest behavior outside the existing local-first retry path.
- Introducing any new output schema or backend annotation policy.

## Constraints

- Keep retry bounded to at most one download attempt per GSE.
- Do not reinterpret a no-sample SOFT as corruption.
- Preserve existing missing-file skip/error behavior.

## Guiding Principle

A valid SOFT file with zero GSM records is a terminal skip condition, not a recoverable
transport failure.

## Ticket File Requirement (MANDATORY)

Create `docs/tickets/ticket-194.md` and paste this ticket verbatim.
