# Ticket #143: Remove `--overrides` option from `geo-gsm-annotate` CLI

## Background

The intended workflow is now explicitly:

1. Prepare a YAML configuration
2. Run `geo-gsm-annotate` on GSE(s)
3. Curate results via the web UI
4. Summarize with `geo-gsm-summarize`

Curator overrides are a **post-processing concern** and must not be injected during
agent execution.

## Problem Statement

`geo-gsm-annotate` currently exposes a `--overrides` option, which allows curator
overrides to be applied during annotation runs. This violates the separation between:

- automated annotation (agent responsibility), and
- human curation (UI + summarization responsibility).

It also introduces ambiguity and irreproducibility in batch workflows.

## Proposed Change

- Remove the `--overrides` option from:
  - CLI argument parsing
  - help text
  - any invocation path in `geo-gsm-annotate`
- Ensure overrides are **only** applied by:
  - the web UI (during curation), and
  - `geo-gsm-summarize` (during export).

No override logic should be reachable during agent execution.

## Policy Impact

* [x] No policy change

This change is purely CLI ergonomics and workflow enforcement.

## Acceptance Criteria

1. `geo-gsm-annotate -h` no longer lists `--overrides`.
2. Passing `--overrides` results in a clear CLI error.
3. Agent execution never applies curator overrides.
4. `geo-gsm-summarize` remains the only CLI entry point that applies overrides.
5. Tests updated or added to ensure overrides are not accepted by `geo-gsm-annotate`.
6. `uv run pytest -q` passes.

## Non-Goals

- No change to override file format.
- No UI changes.
- No summarization behavior changes.

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-143.md` and paste this ticket verbatim.
