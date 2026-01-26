# Ticket #76: Add per-GSE in-memory LLM caching keyed by deterministic context_fingerprint

## Problem

Within large GSEs (especially microarray series), many GSMs are replicate-like and differ only by identifiers (e.g., GSM accession or numeric suffixes in Sample Title). Re-running LLM proposal generation on essentially identical context is slow and wasteful.

We want a deterministic, non-persistent caching mechanism that only reuses LLM outputs for GSMs within the same GSE run when their normalized evidence is identical.

## Scope (minimal, deterministic)

Add an in-memory LLM cache that is:

* **scoped to a single GSE run** (no reuse across different GSEs)
* **non-persistent** (memory only; cleared at end of run)
* keyed by:
  * `gse_accession`
  * model + decoding parameters
  * prompt/template version identifiers
  * `context_fingerprint` (from the deterministic normalizer)

Cache behavior:
* On cache hit, reuse the cached LLM raw output and parsed output for proposal generation.
* Record cache usage in audit artifacts (not in the 8-field final output), including:
  * `llm_cache_hit` boolean per call
  * run-level counts (hits/misses)

Default behavior should remain unchanged unless caching is enabled via config.

No changes to:
* output schema
* validation rules
* decision routing
* ontology grounding semantics
* repair logic

## Acceptance Criteria

1. When enabled, two GSMs within the same GSE run that share the same `context_fingerprint` reuse the LLM result (cache hit).
2. Cache must not be used across different GSE accessions.
3. Audit artifacts indicate cache hits/misses deterministically.
4. When disabled, behavior is unchanged.

## Required Tests

Add regression tests that:
1. Run proposal generation for two GSM inputs under the same GSE with identical fingerprints and assert only one underlying LLM call is made.
2. Run the same two contexts under different GSE accessions and assert no cache reuse occurs.
3. Assert audit records indicate cache hit status.

Run:
`uv run pytest -q`
