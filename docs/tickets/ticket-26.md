# Ticket #26: AGENT-WS-026 — Implement `agent.cli` GSE mode via SOFT (download or local file) and reuse `run_gse_from_jsonl`

## Background

Currently, `agent.cli` exposes a `--gse` option but it is not implemented. Users must manually prepare JSONL context files and use `--jsonl`, even though the codebase already contains ingestion utilities for GEO SOFT files.

Internally, most GSE SOFT files are already downloaded and cached. The CLI should support both online (accession-based) and offline (local SOFT file) workflows while preserving a single downstream execution path.

## Goal

Enable `agent.cli` to process GSE data directly by:

1. Accepting a **GSE accession** and downloading (or reusing cached) SOFT files.
2. Accepting a **local GSE SOFT file** (plain text or `.gz`).
3. Converting SOFT → context JSONL using existing ingest utilities.
4. Reusing the existing `run_gse_from_jsonl(...)` pipeline unchanged.

## Non-goals

* No changes to validation, repair, ontology, or decision logic
* No new execution paths that bypass `run_gse_from_jsonl`
* No redesign of prompts or audit format
* No requirement to support multiple GSEs in one SOFT file (single-GSE scope is sufficient)

## CLI interface

### New / clarified options

* `--gse <GSE_ACCESSION>`

  * Example: `--gse GSE161517`
  * Downloads SOFT if not already cached.

* `--gse-soft <PATH>`

  * Path to a local SOFT file (`.soft`, `.soft.gz`, or equivalent).
  * Must be mutually exclusive with `--gse`.

These options remain mutually exclusive with `--jsonl`, `--gsm`, and `--gsm-file`.

## Implementation plan

### 1. SOFT → context JSONL helper

Add a small helper module under `src/ingest/` (for example `soft_to_context_jsonl.py`) that:

* Accepts either:

  * a `gse_accession`, or
  * a local `soft_path`
* Uses existing components:

  * `ingest/gse_soft_fetcher.py`
  * `ingest/gse_soft_parser.py`
  * `ingest/construct_prompt.py`
* Produces a JSONL file containing records with:

  * `gse_accession`
  * `gsm_accession`
  * `context_text`

### 2. Wrapper functions in `agent/run_gse.py`

Add wrapper functions such as:

* `run_gse_from_accession(gse_accession, cfg, work_dir)`
* `run_gse_from_soft_file(soft_path, cfg, work_dir)`

Each function should:

1. Generate (or reuse) a context JSONL file.
2. Call `run_gse_from_jsonl(jsonl_path, cfg)`.
3. Return `(annotations, audits, flagged, summary)`.

### 3. Cache handling

Support an optional config entry:

```yaml
paths:
  soft_cache_dir: "/path/to/geo_soft_cache"
```

Resolution order for `--gse`:

1. Use SOFT from `paths.soft_cache_dir` if present.
2. Otherwise download via fetcher into a local cache under `output-dir`.
3. Parse from whichever SOFT file is found.

### 4. Update `agent/cli.py`

* Replace the current “GSE mode not implemented” error.
* Route:

  * `--gse` → `run_gse_from_accession`
  * `--gse-soft` → `run_gse_from_soft_file`
* Continue to resolve outputs and summaries exactly as in `--jsonl` mode.

### 5. Tests

Add fast, stub-safe tests:

1. **Local SOFT path**

   * Provide a minimal fake SOFT file in `tmp_path`.
   * Run CLI logic (or underlying function) with `--gse-soft`.
   * Assert non-empty annotations and correct summary.

2. **Cached accession**

   * Pre-populate a temp cache directory with a SOFT file.
   * Configure `paths.soft_cache_dir`.
   * Ensure no network fetch is attempted (monkeypatch fetcher).

All tests should run with:

* `parser.mode = stub`
* `llm.mode = stub`
* `rag.ontology.enabled = false`

## Acceptance criteria

* `agent.cli --gse <GSE>` works end-to-end without requiring manual JSONL preparation.
* `agent.cli --gse-soft <file>` works for both plain and gzipped SOFT files.
* Downstream behavior (audit, repair, outputs) is identical to `--jsonl`.
* Unit tests remain fast and deterministic.
* `uv run pytest -q` passes.

---

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-26.md` and paste this ticket verbatim.
