# Ticket #78: On LLM cache hit, reuse post-grounding canonicalized outputs to avoid recomputation and ensure identical final_output

## Problem

After Ticket #77, LLM and validation are reused on cache hits, but downstream deterministic steps (ontology grounding/canonicalization and final output assembly) are still recomputed or inconsistently applied.

Evidence: for cache-miss vs cache-hit GSMs with identical cached proposal, `canonicalizations` show “Bone marrow” -> “bone marrow” in both, but `final_output.tissue_type` differs (“bone marrow” vs “Bone marrow”). This indicates cache-hit path divergence and wastes time.

## Scope (minimal, deterministic)

Extend the per-GSE in-memory cache entry to store and reuse the complete deterministic post-processing results, including at minimum:

* `validation` (already cached)
* `ontology_matches`
* `canonicalizations`
* `locked_fields`
* `final_output` (canonicalized 8-field output)
* optionally `final_decision`, `flags`, `rationale`, `repair_history`

On cache hit:
* do not rerun grounding/canonicalization/decision assembly for that GSM
* reuse the cached structures and cached `final_output`
* ensure `gsm_accession` is correctly set for the current GSM where applicable
* emit audit markers (audit only): `llm_cache_hit`, `validation_cache_hit`, and `grounding_cache_hit` (or equivalent)

No persistence. Cache remains per-GSE and in-memory.

No changes to:
* schema of canonical outputs
* decision rules
* ontology governance rules

## Acceptance Criteria

1. For two GSMs within a GSE that hit the same cache key, cache-hit and cache-miss outputs are identical for canonicalized fields (e.g., `final_output.tissue_type` casing), except for GSM identifiers.
2. On cache hit, grounding/canonicalization logic is not executed (verified via counters/spies in tests).
3. Audit indicates cache hit and reused steps deterministically.

## Required Tests

Add a regression test that:
1. Processes two GSMs under one GSE with identical fingerprint.
2. Asserts second GSM is a cache hit.
3. Asserts `final_output` matches the first GSM’s post-canonicalization output (excluding gsm_accession).
4. Verifies grounding/canonicalization functions were executed only once.

Run:
`uv run pytest -q`
