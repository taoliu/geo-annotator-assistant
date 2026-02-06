# Ticket #135: Restrict single-LLM reuse to `llm.transport = local_transformers`

## Background

Ticket #134 proposes reusing a single LLM instance across multi-GSE runs in a single
`geo-gsm-annotate` invocation to improve performance and ergonomics.

However, not all LLM transports have the same lifecycle or safety characteristics.
In particular:

- In-process transformer backends (`local_transformers`) are expensive to load and
  safe to reuse.
- Remote or service-based transports (e.g. HTTP, OpenAI-style APIs, llama.cpp HTTP)
  already manage lifecycle externally and should not be implicitly coupled across GSEs.

Reuse must therefore be **explicitly scoped** to safe, local transports.

## Problem Statement

Unconditional reuse of the LLM client across GSEs could:
- introduce unintended coupling for remote transports,
- obscure request-level isolation semantics,
- or complicate future transport-specific behavior.

Reuse must be transport-aware and opt-in by design, not global.

## Proposed Change

Refine the LLM reuse behavior as follows:

1. **Reuse a single LLM instance only when**:
`llm.transport == "local_transformers"`

(string match, case-sensitive, as defined in config schema).

2. For all other `llm.transport` values:
- Preserve current behavior (per-invocation or per-run construction as implemented).
- Do not introduce reuse or shared state implicitly.

3. Implementation guidance:
- Gate reuse logic at the CLI / invocation layer.
- The decision must be made **before** constructing the LLM client.
- Downstream code must not need to know whether reuse is enabled.

4. Help text and/or debug logging (non-user-facing by default) may note:
- whether LLM reuse is enabled
- which transport triggered it

No new config keys are introduced in this ticket.

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change (policy-spec.md must be updated)

This ticket affects only invocation plumbing and performance behavior.
All validation, repair, ontology, and decision semantics remain unchanged.

## Acceptance Criteria

1. When `llm.transport = "local_transformers"`:
- A multi-GSE run (`--gse-file`) constructs the LLM exactly once.
2. When `llm.transport != "local_transformers"`:
- LLM construction behavior is unchanged from current baseline.
3. Outputs for a given GSE are identical whether:
- run alone with `--gse`, or
- run as part of `--gse-file`,
  given the same config and inputs.
4. Unit test added with a stubbed LLM factory:
- `local_transformers` → instantiation count == 1
- non-local transport → instantiation count matches baseline behavior
5. `uv run pytest -q` passes with no regressions.

## Non-Goals

- No changes to prompts, generation parameters, or repair behavior.
- No parallel execution.
- No reuse across separate CLI invocations.
- No changes to UI or reporting.

## Constraints

- Preserve deterministic behavior.
- Preserve GSM/GSE independence.
- Avoid transport-specific branching outside the invocation layer.

## Guiding Principle

**Performance optimizations must respect transport semantics.**
Reuse is allowed only where lifecycle and isolation are fully controlled.

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-135.md` and paste this ticket verbatim.
