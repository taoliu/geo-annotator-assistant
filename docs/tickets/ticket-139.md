# Ticket #139: Reuse a single Chroma client and ontology collections per process invocation

## Background

Ontology grounding uses ChromaDB-backed vector stores (via `src/rag/*` and the ontology
grounders). On cluster GPU nodes with slow shared filesystems, ontology grounding is
observed to be extremely slow. A common cause is repeatedly constructing the Chroma
client and/or reopening collections across many GSMs, which amplifies filesystem I/O.

The system already treats expensive runtime objects as reuse candidates (e.g., LLM
client reuse across batch runs). Chroma client/collection handles should follow the
same “once per process invocation” pattern.

## Problem Statement

If the code constructs the Chroma client or calls `get_or_create_collection()` repeatedly
(per GSM or per field), ontology grounding performance degrades severely on networked
storage due to repeated I/O and cache misses.

We need to ensure:
- Chroma client is constructed once per CLI invocation (process)
- Each ontology collection handle is obtained once and reused for all grounding calls

This must not change any ontology matching/threshold/decision semantics.

## Proposed Change

### 1) Add a process-level Chroma handle cache (client + collections)

Implement a small singleton-style cache in `src/rag/chroma_client.py` (or an adjacent
module) that stores:

- a single initialized Chroma client per `(persist_dir, settings)` (as used today)
- a mapping of `collection_name -> collection_handle` per client

Rules:
- The cache lives in-process only (module-level).
- The cache key must include all config inputs that affect Chroma connection behavior
  (at minimum persist directory and any Chroma settings currently used).
- `get_collection(name)` must return the cached handle if already opened.

### 2) Route ontology grounders through the cached accessors

Audit the call graph for Chroma access (likely starting from `src/rag/ontology_retrieve.py`
and/or the grounders under `src/validator/grounders/`).

Update so that:
- no grounding path constructs a new Chroma client per GSM
- no grounding path reopens the same collection repeatedly

This can be done by:
- passing a shared “rag context” object down from the top-level run entry points,
  OR
- using the module-level cache with deterministic keys (preferred for minimal API churn)

### 3) Maintain determinism and isolation

- No cross-GSE propagation of labels/decisions is introduced.
- Reusing read-only collection handles must not alter results.
- No new caching of query results is introduced in this ticket (only handle reuse).

### 4) Optional: add a lightweight “initialized once” verbose/debug message

If `--verbose` exists (Ticket #138), optionally emit once:
- `INFO: Chroma client initialized (persist_dir=...)`
- `INFO: Chroma collection opened (name=...)`
But only once per process per resource.

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change (policy-spec.md must be updated)

This ticket must not change:
- ontology matching logic
- thresholds
- tie-breaking
- canonicalization and locks
- decision routing
- output schema

It is a performance plumbing change only.

## Acceptance Criteria

1. In a batch run grounding multiple GSMs, the Chroma client is initialized once per
   process invocation for a given config/persist directory.
2. For each ontology collection used (EFO/Uberon/DOID/NCIT/Cellosaurus as applicable),
   the collection handle is opened at most once per process invocation.
3. Ontology grounding outputs for a GSM are identical before vs after this change,
   given identical inputs and config (determinism preserved).
4. Add a unit test using monkeypatch/stubs to count initializations:
   - client init count == 1 across multiple grounding calls
   - collection open count == 1 per collection across multiple grounding calls
5. `uv run pytest -q` passes.

## Non-Goals

- No “load entire vector DB into RAM” feature.
- No change to where Chroma persists its files.
- No parallelism changes.
- No query-result memoization or caching.

## Constraints

- Read-only semantics only.
- Cache key must be correct to avoid mixing different persist dirs/configs.
- Avoid hidden behavior changes; keep code paths explicit and testable.

## Guiding Principle

Reuse expensive read-only resources per process invocation to reduce filesystem I/O,
without changing semantics.

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-139.md` and paste this ticket verbatim.
