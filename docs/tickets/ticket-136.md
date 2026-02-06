# Ticket #136: Support local GEO SOFT mirror via config (skip missing files, no hard fail)

## Background

When `geo-gsm-annotate` is invoked with `--gse` or `--gse-file`, the ingest layer
currently fetches GEO SOFT files from the remote NCBI GEO HTTPS endpoint using
a deterministic path rule (`src/ingest/gse_soft_fetcher.py:get_remote_path`).

In our environment, GEO SOFT files are already mirrored locally in a directory
tree that matches GEO’s `GSEnnn` grouping scheme. We need a config option to
use this local mirror by default (when available), without changing any backend
validation/repair/ontology/decision logic.

## Problem Statement

Remote fetching is slow and unnecessary when a local SOFT mirror exists.
In addition, missing local files should not cause the entire batch run to fail.
Instead, the tool should warn and continue, skipping the missing GSE.

## Proposed Change

Add an optional config setting under ingest (or another existing allowed namespace
if ingest is already present in the config schema) to enable local SOFT resolution.

### New config key (preferred)

```yaml
ingest:
  geo_soft_local_dir: "/abs/path/to/geo/soft/mirror"
````

Semantics:

* If `ingest.geo_soft_local_dir` is set and non-empty:

  * For `--gse` / `--gse-file` processing, attempt to locate the SOFT file locally
    first using the deterministic mapping below.
  * If the local file exists, use it (no remote fetch).
  * If the local file does not exist, emit a user-visible warning and skip that GSE.
  * Do not fall back to remote fetch in this ticket (explicitly out of scope unless
    added later as a separate ticket with an explicit option).

* If `ingest.geo_soft_local_dir` is not set:

  * Preserve current behavior (remote fetch).

### Local path resolution

Implement a helper (or integrate into existing fetcher) equivalent to:

```python
def get_local_path(geo_id: str, local_dir: str) -> str:
    file_path = ""
    try:
        assert geo_id[:3] == "GSE"
        assert geo_id[3:].isdigit()
        dir_name_n = int(geo_id[3:]) // 1000
        if dir_name_n == 0:
            dir_name = "GSEnnn"
        else:
            dir_name = f"GSE{dir_name_n}" + "nnn"
        file_path = f"{local_dir}/{dir_name}/{geo_id}_family.soft.gz"
    except AssertionError:
        pass
    return file_path
```

Note: reuse the same grouping logic as remote path generation to keep behavior
deterministic and auditable.

### Missing file behavior (batch-safe)

If the resolved local file path does not exist:

* Print a clear message to stderr (or logger warning), e.g.:

  * `WARNING: GEO SOFT file not found for GSE12345 at <path>; skipping.`
* Continue processing the remaining GSEs.
* For single `--gse`, exit code behavior must remain consistent with existing CLI
  conventions. If current behavior is "hard fail", this ticket changes only the
  ingest step to be non-fatal when local mirror is enabled. The final exit code
  rules should be documented in acceptance criteria tests.

### Documentation / help updates

* Update README (or a CLI usage section if one exists) to mention the new config key.
* No new CLI flags are introduced in this ticket.

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change (policy-spec.md must be updated)

This ticket affects only ingest source selection (local file vs remote download)
and batch robustness. It must not change annotation semantics or outputs given the
same input SOFT content.

## Acceptance Criteria

1. Config schema accepts `ingest.geo_soft_local_dir` (with validation that it is a string).
2. When `ingest.geo_soft_local_dir` is set:

   * GSE processing reads SOFT from the local mirror if present.
   * No network fetch is attempted for that GSE.
3. When the local SOFT file is missing:

   * A warning is emitted.
   * The GSE is skipped and the run continues for other GSEs.
4. When `ingest.geo_soft_local_dir` is not set:

   * Current remote fetching behavior is unchanged.
5. Add unit tests (likely in ingest tests or CLI/batch tests) that:

   * verify correct local path mapping for representative GSE IDs
   * verify missing local file triggers "skip" rather than crash
6. `uv run pytest -q` passes.

## Non-Goals

* No change to remote path rules.
* No introduction of remote fallback after local miss (unless added later).
* No changes to downstream parsing, validation, repair, ontology grounding, or decisions.
* No UI changes.

## Constraints

* Deterministic mapping only.
* Batch behavior must never be implicit beyond the explicit GSE list.
* Skips must be user-visible and auditable (at least via logs/stderr).

## Guiding Principle

Prefer explicit, reproducible inputs and robust batch processing over implicit network behavior.

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-136.md` and paste this ticket verbatim.
