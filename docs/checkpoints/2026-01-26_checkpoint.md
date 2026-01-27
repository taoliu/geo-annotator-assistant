# Checkpoint — 2026-01-26 (v0.8 Completed)

**v0.8 completed.**

## Purpose

This checkpoint captures the authoritative project state after milestone **v0.8 (backend robustness & correctness sweep)**.

It is a stable reset point for resuming work without revisiting completed backend fixes.

---

## Current State Summary

* v0.8 is complete.
* Backend is stable and deterministic.
* UI remains out of scope for this milestone and unchanged.

---

## Configuration Additions (v0.8)

* `llm_cache.enabled: false` by default (deterministic per-GSE caching when enabled)
* `rag.ontology.data_type.fallback_allowlist_enabled`
* `rag.ontology.data_type.fallback_allowlist` (Microarray allowlist)

---

## Behavioral Invariants Reinforced

* Canonical output is **exactly 8 fields** in `annotations.jsonl`.
* `audit.jsonl`, `curation.jsonl`, `gse_consistency.json`, and `gse_field_values.jsonl` are derived, diagnostic artifacts.
* Consistency flags do **not** drive repairs (notably `healthy_disease_conflict`).
* `primary_failure` is reported only for repair-triggering failures.

---

## Tests

Expected test status:

```
uv run pytest -q
```

---

## Status

**Checkpoint status:** ACTIVE
