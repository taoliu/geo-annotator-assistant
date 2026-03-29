# Ticket #195: Remove stray `REQUIRED_KEY` import-time failure in `run_single.py`

## Background

Recent test runs fail during collection before any GSM pipeline logic executes.

The failure originates while importing `src/agent/run_single.py`, which is a core
dependency for batch, GSE, and CLI test modules.

## Problem Statement

`src/agent/run_single.py` currently contains a stray top-level bare identifier:

`REQUIRED_KEY`

Because `REQUIRED_KEY` is not defined anywhere, Python raises an import-time
`NameError` during module evaluation. This prevents test collection and blocks any
workflow that imports `run_single.py`.

## Proposed Change

Remove the stray `REQUIRED_KEY` line from `src/agent/run_single.py`.

No behavioral change is intended beyond restoring successful module import and normal
test collection.

## Layer Affected

- [ ] Canonicalization
- [ ] Ontology grounding
- [ ] Validation / Repair
- [ ] Decision routing
- [ ] UI only
- [ ] Documentation only

Core runner import hygiene only.

## Policy Impact

- [x] No policy change
- [ ] Policy clarification only
- [ ] Policy change (policy-spec.md must be updated)

This ticket removes an accidental import-time regression only. It must not alter
annotation semantics, pipeline ordering, schema, or audit behavior.

## Acceptance Criteria

1. `src/agent/run_single.py` imports without raising `NameError`.
2. `uv run pytest -q` no longer fails during collection because of `REQUIRED_KEY`.
3. No pipeline semantics are changed.

## Non-Goals

- Any refactor of required-key handling.
- Any change to validation, repair, ontology, or CLI behavior.

## Constraints

- Keep the fix minimal and local to the accidental regression.
- Do not introduce any unrelated behavior changes while restoring importability.

## Guiding Principle

Import-time failures caused by accidental stray code should be removed with the
smallest possible change.

## Ticket File Requirement (MANDATORY)

Create `docs/tickets/ticket-195.md` and paste this ticket verbatim.
