# Ticket #52: RAG-ONTO-010 — Add configurable embedding device for Chroma query embedding (cpu/cuda/mps)

## Background

The Chroma query path uses `SentenceTransformerEmbeddingFunction`. The device must be configurable to support `cpu`, `cuda`, and `mps` reliably across environments.

---

## Scope (STRICT)

### In scope

1. Extend config schema to add:

* `rag.ontology.embedding.model_name` (if not already present)
* `rag.ontology.embedding.device` with allowed values: `cpu`, `cuda`, `mps`

2. Update `src/rag/chroma_client.py` collection initialization to use:

```python
embedding_function = SentenceTransformerEmbeddingFunction(
    model_name=model_name,
    device=device,
)
```

3. Default behavior:

   * if device not specified, default to `cpu` (or keep current default if explicitly documented elsewhere)
   * validation: if an unknown device is set, raise a clear config error early

### Out of scope

* Auto-detecting GPUs
* Any change to retrieval logic or scoring

---

## Acceptance Criteria

1. Setting `rag.ontology.embedding.device: cuda` uses CUDA when available (covered by unit test via constructor argument inspection/mocking).
2. Setting `mps` passes through correctly.
3. Existing tests pass.

---

## Tests Required

Add `tests/test_chroma_embedding_device_config.py`:

* Mock `SentenceTransformerEmbeddingFunction` and assert it receives the configured `device` argument.
* Validate config parsing rejects invalid values.

---

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-52.md` and paste this ticket verbatim.

---
