# Ticket #17-b: AGENT-WS-017b — Fix ontology ChromaDB query path, embedding conflict, and dependencies

You are working in repo `geo-gsm-annotator-agent`.

## Context

Ontology grounding (AGENT-WS-017) was implemented and unit tests pass, but **runtime grounding fails** with `ONTOLOGY_INDEX_UNAVAILABLE`. Manual debugging identified the root causes:

1. The persisted ChromaDB collection `ontology_rag` was built with a **default embedding configuration**, so Chroma **rejects `get_collection(..., embedding_function=...)`**.
2. The correct and proven query pattern (used in `rag_ontologies`) is:

   * open collection **without** embedding function
   * compute query embedding manually
   * call `collection.query(query_embeddings=[...])`
3. Required runtime dependencies were missing from `pyproject.toml`.
4. `pytest` is not declared as a dependency, preventing Codex from running tests autonomously.

This ticket fixes these issues so ontology grounding works end-to-end.

---

## Goals

* Make ontology grounding actually query the existing ChromaDB (`ontology_rag`) without embedding conflicts
* Align query logic exactly with the known-good `rag_ontologies` implementation
* Add missing dependencies so Codex can run `pytest` without manual intervention
* Eliminate false `ONTOLOGY_INDEX_UNAVAILABLE` audit entries when DB is present

---

## Non-goals

* Do not rebuild or modify the ontology ChromaDB
* Do not change the 8-field annotation schema
* Do not redesign ontology matching logic (selection logic stays as-is)

---

## A) Fix ontology retrieval implementation (CRITICAL)

### Files

* `src/rag/ontology_retrieve.py` (or equivalent retrieval module)
* Any helper that opens a Chroma collection for ontology grounding

### Required changes

**1. Do NOT pass an embedding function to `get_collection()`**

Replace any code like:

```python
client.get_collection(
    name=collection_name,
    embedding_function=embedding_fn,
)
```

with:

```python
client.get_collection(name=collection_name)
```

This is mandatory. Passing an embedding function causes:

```
ValueError: embedding function conflict: new vs persisted: default
```

---

**2. Compute query embeddings manually**
Use the same pattern as `rag_ontologies`:

```python
from langchain_huggingface import HuggingFaceEmbeddings

embedder = HuggingFaceEmbeddings(
    model_name="BAAI/bge-base-en-v1.5",
    encode_kwargs={"normalize_embeddings": True},
)

query_embedding = embedder.embed_query(query_text)

results = collection.query(
    query_embeddings=[query_embedding],
    n_results=top_k,
    where={"source": source_name},
)
```

Notes:

* `where={"source": source_name}` must match ontology metadata exactly
* Do not use `query_texts=...` for this persisted collection

---

**3. Error handling**

* Only treat failures as `ONTOLOGY_INDEX_UNAVAILABLE` if:

  * DB path missing
  * SQLite cannot be opened
  * Collection name missing
* Do NOT treat embedding conflicts as index unavailable (they should not occur after this fix)

---

## B) Ensure ontology grounding uses the fixed retrieval path

### Files

* `src/validator/grounders/*.py`
* `src/validator/ontology_validator.py`

Verify:

* All ontology-backed fields (`tissue_type`, `disease`, `cell_line`, `data_type`) go through the fixed retrieval function
* Retrieved metadata fields are read from:

  * `metadata["term_id"]`
  * `metadata["label"]`
  * `metadata["source"]`
* `status = INDEX_UNAVAILABLE` should no longer appear when DB is present and readable

---

## C) Dependency fixes (MANDATORY)

### File

* `pyproject.toml`

Add the following dependencies if missing:

```toml
dependencies = [
    ...
    "langchain-huggingface",
    "sentence-transformers",
    "pytest",
]
```

Rationale:

* `langchain-huggingface` is required for `HuggingFaceEmbeddings`
* `sentence-transformers` is required under the hood
* `pytest` must be present so Codex can run tests autonomously

Do NOT assume these are installed implicitly.

---

## D) Add a regression test for embedding conflict

Add a small test to ensure ontology retrieval does not pass an embedding function into `get_collection`.

### Suggested test

* File: `tests/test_ontology_chroma_runtime_query.py`
* Use monkeypatch or a fake client to assert:

  * `get_collection(name=...)` is called **without** `embedding_function`
  * `collection.query(query_embeddings=[...])` is used

This test should fail if someone reintroduces `query_texts` or `embedding_function` usage.

---

## E) Acceptance criteria

All must be true:

1. The following sanity query works without error:

```python
collection = client.get_collection("ontology_rag")
collection.query(query_embeddings=[embedding], where={"source": "Human Disease Ontology"})
```

2. Running the agent on a real GSM no longer produces `ONTOLOGY_INDEX_UNAVAILABLE` when DB exists

3. Audit output shows:

   * non-null `matched_term_id`
   * `status: MATCHED | AMBIGUOUS | LOW_CONFIDENCE` (not INDEX_UNAVAILABLE)

4. Codex can run:

```bash
pytest -q
```

without manual dependency installation

---

## F) Developer note (DO NOT IGNORE)

This repository **must** follow the persisted-Chroma query pattern used by `rag_ontologies`. Any attempt to let Chroma handle embeddings internally for this DB will fail by design.

---

### Reference behavior (known-good)

The following pattern is correct and should be mirrored:

```python
collection = chroma_client.get_collection("ontology_rag")
query_embedding = embedding_function.embed_query(query_text)
collection.query(query_embeddings=[query_embedding])
```

