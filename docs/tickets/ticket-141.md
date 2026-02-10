# Ticket #141: If local SOFT is missing or fails to parse, re-download to repository and retry once

## Background

We maintain a local repository/mirror of GEO GSE family SOFT files. The ingest pipeline
prefers local files to avoid repeated remote downloads.

However, local repositories can contain:
- missing files, or
- corrupted / truncated files from incomplete earlier downloads

When this happens, the current behavior either skips, errors, or falls back to remote
depending on configuration. We want a robust behavior: if the local file is missing
or cannot be parsed correctly, we should fetch a fresh copy from remote, store it
into the repository directory, and retry parsing.

## Problem Statement

Batch runs are fragile when a local SOFT file is incomplete. The run either fails or
skips even though a correct remote copy is available. The system should be able to
self-heal the local repository for these cases.

## Proposed Change

Extend the local-first SOFT resolution logic as follows for `--gse` / `--gse-file`
processing when a local repository directory is configured.

### Config dependency

This ticket assumes the presence of:
- a configured local repository dir (e.g. `ingest.geo_soft_local_dir`)
- remote download support (ftp/https) already exists

No new config keys are required in this ticket, but it must respect existing settings:
- remote transport selection (ftp vs https)
- missing-file policy (remote/skip/error) for cases where remote fetch is disallowed

### New behavior: retry-on-missing-or-parse-failure (local repository mode)

For each GSE:

1. Resolve local SOFT path deterministically under the repository directory.

2. Attempt to read and parse the local file:
   - If the local file does not exist:
     - handle as "missing local"
   - If the local file exists but parsing fails (including gzip errors, truncated reads,
     parser exceptions, or "incomplete content" detection if available):
     - handle as "parse-failed local"

3. For missing local OR parse-failed local:
   - If the configured missing-file policy allows remote (e.g. "remote"):
     - download the SOFT file from remote
     - write it to the repository directory at the deterministic local path
       (overwriting any existing corrupted file)
     - retry parsing exactly once using the newly downloaded file
   - If remote fetch is not allowed (e.g. policy is "skip" or "error"):
     - preserve the existing behavior (skip or raise), but the message must clearly
       indicate whether the failure was "missing" or "parse-failed".

4. If the re-download attempt succeeds but parsing still fails:
   - treat it as a hard parse failure:
     - skip or error according to configured policy (or existing baseline handling),
       but do not loop further.

### Runtime messages

Emit user-visible messages (stderr/logger), at minimum:
- `INFO: GSE12345: using local SOFT <path>`
- `WARNING: GSE12345: local SOFT missing; downloading fresh copy`
- `WARNING: GSE12345: local SOFT parse failed (<reason>); re-downloading fresh copy`
- `INFO: GSE12345: re-download complete; retrying parse`
- `ERROR/WARNING: GSE12345: parse failed after re-download; skipping/aborting`

Do not print SOFT content.

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change (policy-spec.md must be updated)

This ticket changes only ingest robustness. It must not change annotation semantics,
pipeline order, output schema, or decision logic.

## Acceptance Criteria

1. When local file is missing and remote fallback is allowed:
   - file is downloaded to the repository path
   - parsing is retried once
2. When local file exists but is corrupted/unparsable:
   - a re-download is performed to the same repository path (overwrite)
   - parsing is retried once
3. If parsing still fails after re-download:
   - behavior follows configured policy (skip or error), and no infinite retries occur
4. Remote transport selection (ftp vs https) is respected.
5. Tests added:
   - missing local triggers download + retry (using stubs/mocks)
   - parse failure triggers overwrite download + retry (simulate gzip/parser error)
   - second parse failure does not retry again
6. `uv run pytest -q` passes.

## Non-Goals

- No changes to SOFT parsing rules or extraction semantics.
- No changes to validation/repair/ontology behavior.
- No parallel downloads.

## Constraints

- Retry is at most once per GSE per run to avoid loops.
- Overwrite corrupted local file only when re-downloading is triggered.

## Guiding Principle

Prefer deterministic local repositories, but self-heal when local artifacts are incomplete.

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-141.md` and paste this ticket verbatim.
