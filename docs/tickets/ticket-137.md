# Ticket #137: Local-first GEO SOFT resolution with remote fallback and configurable download transport (ftp/https)

## Background

When `geo-gsm-annotate` processes `--gse` or `--gse-file`, it obtains a GSE family SOFT
file using a deterministic remote path rule (currently in `src/ingest/gse_soft_fetcher.py`).
In our environment, SOFT files are already mirrored locally in a directory structure that
matches GEO’s `GSEnnn` grouping scheme, so local reads should be preferred.

We also need:
- a clean, explicit fallback to remote download when the local mirror is missing
- a configuration knob to select remote download transport (`ftp` vs `https`)
- runtime messages indicating whether each GSE is served from local or remote

## Problem Statement

Current behavior always attempts remote download (unless user supplies `--gse-soft`).
This is slow and unnecessary when local mirrors exist. Missing local files should not
break batch runs, and the user should be able to choose ftp vs https remote download.

## Proposed Change

Introduce ingest configuration options to control SOFT resolution and download method.

### Config additions (YAML)

```yaml
ingest:
  geo_soft_local_dir: "/abs/path/to/geo/soft/mirror"   # optional
  geo_soft_on_missing: "remote"                        # one of: "remote" | "skip" | "error"
  geo_soft_remote_transport: "https"                   # one of: "https" | "ftp"
```

Semantics:

* If `ingest.geo_soft_local_dir` is set and non-empty:

  * Resolve a deterministic local path for each GSE (see Local Path Resolution).
  * If the file exists locally: use it.
  * If missing locally: apply `ingest.geo_soft_on_missing`:

    * `"remote"`: download from GEO using configured transport (ftp/https) then use the downloaded file.
    * `"skip"`: emit warning and skip this GSE (continue batch).
    * `"error"`: raise a clear error and stop the run.
* If `ingest.geo_soft_local_dir` is not set:

  * Preserve current behavior (remote download), but the remote transport may be chosen
    via `ingest.geo_soft_remote_transport` (default "https").

### Local Path Resolution

Implement deterministic local mapping:

* directory grouping matches GEO scheme (`GSEnnn`, `GSE1nnn`, `GSE2nnn`, ...):

  * `dir_name_n = int(geo_id[3:]) // 1000`
  * `dir_name = "GSEnnn"` if `dir_name_n == 0`, else `f"GSE{dir_name_n}nnn"`
* local path:

  * `<local_dir>/<dir_name>/<GSE>_family.soft.gz`

### Remote download transport selection

The fetcher must select one of the existing methods:

* `download_file_via_https(remote_file_path, local_file_path, base_url="https://ftp.ncbi.nih.gov", ...)`
* `download_file_via_ftp(remote_file_path, local_file_path, ftp_server="ftp.ncbi.nih.gov", ...)`

Selection rule:

* If `ingest.geo_soft_remote_transport == "https"` → use https function.
* If `"ftp"` → use ftp function.
* Any other value → config validation error (fail fast).

Remote path mapping remains unchanged (still derived by `get_remote_path(geo_id)`).

### Runtime messages

Add clear, concise runtime messages while processing each GSE SOFT:

* When starting a GSE:

  * `INFO: GSE12345: resolving SOFT (local-first)`
* If local hit:

  * `INFO: GSE12345: using local SOFT at <path>`
* If local miss and fallback remote:

  * `WARNING: GSE12345: local SOFT missing at <path>; downloading via https`
  * `INFO: GSE12345: downloaded SOFT to <path>`
* If local miss and skip:

  * `WARNING: GSE12345: local SOFT missing at <path>; skipping (geo_soft_on_missing=skip)`
* If local miss and error:

  * `ERROR: GSE12345: local SOFT missing at <path>; aborting (geo_soft_on_missing=error)`

Notes:

* Messages should go to stderr or the project logger (prefer logger if already used).
* Keep message formats stable to support grepping in batch logs.

### Output location for downloaded SOFT

If downloading is required and `geo_soft_local_dir` is set:

* Download to the same deterministic local mirror path (create parent dirs as needed).
  This ensures future runs are faster and reproducible.

If `geo_soft_local_dir` is not set:

* Preserve existing download destination behavior (whatever current code uses for downloads).

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change (policy-spec.md must be updated)

This ticket affects ingest source selection and download transport only. It must not
change prompt construction, validation, repair, ontology grounding, decision routing,
or output schema.

## Acceptance Criteria

1. Config schema supports:

   * `ingest.geo_soft_local_dir` (string, optional)
   * `ingest.geo_soft_on_missing` in {"remote","skip","error"} (default "remote")
   * `ingest.geo_soft_remote_transport` in {"https","ftp"} (default "https")
2. With `geo_soft_local_dir` set:

   * local hit uses local file without remote download
   * local miss + on_missing=remote downloads via selected transport and then uses file
   * local miss + on_missing=skip emits warning and continues batch
   * local miss + on_missing=error stops with clear error
3. With `geo_soft_local_dir` unset:

   * behavior matches baseline remote fetch logic, except remote transport selection is honored
4. Runtime messages appear for each GSE indicating local vs remote source (and transport when remote).
5. Tests added:

   * local path mapping correctness for representative GSE IDs
   * remote transport selection toggles the chosen downloader (use monkeypatch/stub)
   * skip vs error vs remote behavior on missing local file
6. `uv run pytest -q` passes.

## Non-Goals

* No changes to remote path derivation logic.
* No parallel downloads.
* No UI changes.
* No changes to any backend decision semantics.

## Constraints

* Deterministic mapping only.
* Batch semantics must remain explicit (GSE list is explicit input).
* Download transport must be config-controlled and validated.

## Guiding Principle

Prefer reproducible local inputs, with explicit and auditable remote fallback when needed.

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-137.md` and paste this ticket verbatim.
