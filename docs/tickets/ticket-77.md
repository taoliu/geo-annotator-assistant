# Ticket #77: On LLM cache hit, reuse cached validation results and skip re-validating identical proposals

## Problem

We added per-GSE LLM caching. On cache hits, we reuse the same LLM proposal, so validation would deterministically produce the same result. Re-running validation is wasted work.

We want to skip redundant validation while preserving auditability (must record `llm_cache_hit`).

## Scope (minimal, deterministic)

When LLM cache hit occurs:

1. Reuse the cached parsed proposal output.
2. Reuse the cached validation result associated with that proposal (format/semantic/consistency structures as currently stored in audit).
3. Skip executing the validation code path again.
4. Ensure audit artifacts record:
   * `llm_cache_hit: true` for the proposal step
   * optional `validation_cache_hit: true` if you distinguish them (audit only)

Cache key must include all inputs that affect proposal interpretation and validation outcomes, including:
* prompt/template version
* validator version
* relevant config hashes if applicable

No changes to:
* decision routing
* ontology grounding semantics
* output schema

## Acceptance Criteria

1. On cache hit, validation code is not executed and cached validation results are reused.
2. Audit records clearly show `llm_cache_hit: true` (and validation cache hit if implemented).
3. When cache is disabled, behavior is unchanged.
4. Determinism preserved.

## Required Tests

Add a regression test that:
1. Runs two GSMs within the same GSE that share the same fingerprint and trigger a cache hit.
2. Asserts that validation is executed only once (e.g., via a counter/spy/mock).
3. Asserts the second GSM audit indicates `llm_cache_hit: true`.

Run:
`uv run pytest -q`
