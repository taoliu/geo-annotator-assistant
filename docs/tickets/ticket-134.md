# Ticket #134: Reuse a single LLM client across multi-GSE runs in one CLI invocation

## Background

The agent supports GSE-scale processing and already has batch-like workflows (e.g., `--input-dir` in UI and existing batch runners). For CLI batch processing via the new `--gse-file`, repeatedly constructing the LLM client per GSE is expensive and unnecessary.

## Problem Statement

When processing multiple GSEs in one run, the LLM should be instantiated once and reused for the entire invocation, without changing inference behavior or outputs.

## Proposed Change

Refactor the CLI invocation path (and any invoked runner) so that:

- The LLM client (and any associated immutable runtime objects such as prompt loader / tokenizers if applicable) is created exactly once per `geo-gsm-annotate` process.
- The same client instance is passed into each per-GSE run.
- Per-GSE state remains isolated (no cross-GSE propagation of labels, decisions, or overrides).

Implementation constraints:
- No changes to prompts, generation parameters, repair loop limits, decision routing, or ontology logic.
- Any caches must remain read-only or keyed such that they do not change semantics across GSEs (existing behavior only).

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change (policy-spec.md must be updated)

This ticket is a performance/ergonomics change to invocation plumbing only. All policy-governed behavior remains identical.

## Acceptance Criteria

1. In a `--gse-file` run, the LLM client is constructed once (verify via a single log line, debug counter, or test stub).
2. Outputs for a given GSE are identical whether run alone (`--gse`) or as part of a multi-GSE run (`--gse-file`), given the same config and inputs.
3. Unit test added using a stubbed LLM factory that counts instantiations:
   - Expected count == 1 for multi-GSE run
   - Expected count == 1 for single-GSE run
4. No test regressions: `uv run pytest -q` passes.

## Non-Goals

- No attempt to share ontology retrieval results across runs beyond existing caches.
- No parallel execution changes.
- No changes to `geo-gsm-ui`.

## Constraints

- Preserve deterministic behavior.
- Preserve GSM/GSE independence (no propagation).
- Keep audit artifacts accurate and per-GSE.

## Guiding Principle

Performance improvements are allowed only when they do not change semantics.

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-134.md` and paste this ticket verbatim.
