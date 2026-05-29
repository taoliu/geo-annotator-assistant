# Ticket #200: Rename public CLI commands to gaa prefix

## Background

The project has been renamed to **GEO Annotator Assistant**. The public command-line
entry points should use the shorter `gaa` prefix, where `gaa` stands for
GEO Annotator Assistant.

## Problem Statement

The package still installs and documents command names with the old `geo-gsm-*`
prefix:

- `geo-gsm-annotate`
- `geo-gsm-summarize`
- `geo-gsm-ui`

This keeps the old project identity visible in current user-facing command
surfaces.

## Proposed Change

Rename the public console scripts:

- `geo-gsm-annotate` -> `gaa-annotate`
- `geo-gsm-summarize` -> `gaa-summarize`
- `geo-gsm-ui` -> `gaa-ui`

Update current user-facing documentation, CLI help examples, and tests to use the new
command names.

## Layer Affected

- [ ] Canonicalization
- [ ] Ontology grounding
- [ ] Validation / Repair
- [ ] Decision routing
- [ ] UI only
- [x] CLI / documentation only

## Policy Impact

- [x] No policy change
- [ ] Policy clarification only
- [ ] Policy change

This ticket changes public invocation names only. It must not alter backend
annotation semantics, schemas, validation, repair, audit, or UI authority boundaries.

## Acceptance Criteria

1. `pyproject.toml` installs `gaa-annotate`, `gaa-summarize`, and `gaa-ui`.
2. README and current handoff docs use the new command names.
3. CLI help/examples use `gaa-annotate`.
4. Tests that assert documented command text are updated.
5. `uv lock` passes.
6. `uv run pytest -q` passes.

## Non-Goals

- Renaming Python modules or package import paths.
- Changing subcommand names such as `standardize-terms`.
- Rewriting historical tickets, milestones, or checkpoints that document previous
  command names at the time they were created.
