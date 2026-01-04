Ticket #17-d: AGENT-WS-017d — Consolidate ontology grounding config under `rag.*` (canonical schema), update code + example configs + docs guardrails

You are working in repo `geo-gsm-annotator-agent`.

## Context

Earlier milestones established a `rag:` config block as a **format placeholder**. Recent ontology grounding work introduced new **top-level** config keys (`ontology_chroma_*`, `ontology_sources_by_field`, etc.), which created inconsistency across the repo and future confusion.

We want a single canonical config layout:

* Keep the **`rag:` namespace format**
* Replace placeholder content with **correct, current ontology-Chroma grounding settings**
* Update code to read from `rag.*` (not top-level)
* Add documentation rules to prevent future config drift across ChatGPT/Codex sessions

Important: the old `rag:` placeholder values may be wrong; only keep the *namespace format*, not the content.

## Goal

1. Make `rag.*` the only canonical location for ontology grounding configuration
2. Update `config/example_config.yaml` and `config/llama3-1b_config.yaml` accordingly
3. Update config parsing/loading code to use `rag.*` keys
4. Add a compatibility shim (optional but recommended) that maps old top-level `ontology_*` keys into `rag.ontology.*` with a deprecation warning
5. Add “config stability” instructions to docs so future ticket generation does not reintroduce inconsistencies

## Non-goals

* Do not change the agent output schema (8 fields).
* Do not redesign ontology retrieval or scoring logic.
* Do not rebuild the ontology ChromaDB.

---

## Canonical config schema (to implement)

### YAML structure (canonical)

Replace top-level ontology keys with:

```yaml
rag:
  persist_path: "ontology_chroma_db"          # directory containing chroma.sqlite3
  collection_name: "ontology_rag"             # collection inside Chroma
  k: 20                                       # top-K retrieval

  ontology:
    enabled: true

    embedding:
      provider: "langchain_huggingface"       # embeds queries manually
      model_name: "BAAI/bge-base-en-v1.5"
      normalize_embeddings: true

    sources_by_field:
      tissue_type: "Uberon Ontology"
      disease: "Human Disease Ontology"
      cell_line: "Cellosaurus"
      data_type: "Experimental Factor Ontology"

    thresholds:
      min_confidence_to_accept: 0.80
      max_delta_for_ambiguity: 0.05
```

Notes:

* `rag.persist_path` refers to the directory that contains `chroma.sqlite3`.
* `rag.collection_name` is the collection name (always `ontology_rag` for now).
* Retrieval uses manual embedding + `query_embeddings=[...]` and must not pass embedding_function into `get_collection`.
* `rag.k` is the shared default for ontology top_k.

---

## Tasks

### A) Update config model / loader

Files:

* `src/agent/config.py` (and any config schema definitions)

Actions:

1. Define a `RagConfig` object with:

   * `persist_path: str`
   * `collection_name: str`
   * `k: int`
   * `ontology: OntologyRagConfig`

2. Define `OntologyRagConfig`:

   * `enabled: bool`
   * `embedding: EmbeddingConfig`
   * `sources_by_field: dict[str, str]`
   * `thresholds: ThresholdConfig`

3. Ensure YAML parsing supports these nested fields and the defaults are sensible.

### B) Update ontology retrieval code to read `rag.*`

Files:

* `src/rag/ontology_retrieve.py` (or equivalent)
* Any grounder/validator that currently reads top-level `ontology_*`

Actions:

* Replace usage of:

  * `ontology_chroma_db_path` -> `cfg.rag.persist_path`
  * `ontology_chroma_collection` -> `cfg.rag.collection_name`
  * `ontology_top_k` -> `cfg.rag.k`
  * embedding model/normalize -> `cfg.rag.ontology.embedding.*`
  * sources_by_field -> `cfg.rag.ontology.sources_by_field`
  * thresholds -> `cfg.rag.ontology.thresholds`

### C) Compatibility shim for old configs (recommended)

Purpose: if users still have old top-level ontology keys, pipeline should not break.

Implementation:

* In config loading, if `rag.ontology` block is missing but top-level `ontology_chroma_enabled` (or other ontology_* keys) exist:

  * map them into the new structure in-memory
  * print a single warning:

    * “Deprecated config: move ontology_* keys under rag.ontology.*”
* If both are present, prefer `rag.*` and optionally warn that top-level keys are ignored.

This avoids another “split brain” future.

### D) Update example config files

Files:

* `config/example_config.yaml`
* `config/llama3-1b_config.yaml`

Actions:

* Remove all top-level `ontology_*` keys
* Add the canonical `rag:` block with correct values as above
* Ensure the YAML remains runnable and points to correct relative path by default (`ontology_chroma_db`)

### E) Update docs to prevent future inconsistency

Files:

* `docs/whitepaper.md` (preferred)
* optionally `docs/RESUME.md`

Add a short section “Config stability contract”:

Required points:

* Retrieval/grounding configuration must live under `rag.*`
* Do not introduce new top-level config namespaces for retrieval features
* Any ticket that changes config must also update:

  * `src/agent/config.py`
  * both example configs under `config/`
  * at least one test that loads config (to prevent drift)

Also add one line for future ChatGPT/Codex sessions:

* “Before generating tickets that modify config schema, inspect current example configs and config model, and follow existing namespaces.”

### F) Tests

Add or update tests to ensure the new schema loads.

Files:

* Add `tests/test_config_rag_schema.py` (or extend an existing config loading test)

Test cases:

1. Loading new canonical config from `config/example_config.yaml` succeeds and exposes:

   * `cfg.rag.persist_path`
   * `cfg.rag.collection_name`
   * `cfg.rag.k`
   * `cfg.rag.ontology.enabled`
2. Backward compatibility (if shim implemented):

   * Build a minimal YAML dict with old top-level `ontology_*` keys and ensure it loads and maps into `cfg.rag.ontology.*`

---

## Acceptance criteria

* Running `uv run python -m agent.cli --config config/llama3-1b_config.yaml --jsonl <file> --output-dir <out>` works with ontology grounding enabled.
* No code path reads top-level `ontology_*` keys as the primary source of truth.
* Both example configs use only the canonical `rag.*` schema.
* Tests pass (`pytest -q`).
* Docs include config stability guidance.

---

## Developer notes

* Keep `rag` block as the canonical namespace even if future RAG retrieval is expanded beyond ontology grounding.
* Do not reintroduce `rag.collections.{EFO,UBERON,...}` placeholders unless the implementation actually uses separate collections. For now, a single `collection_name: ontology_rag` is the correct representation of current work.

---
