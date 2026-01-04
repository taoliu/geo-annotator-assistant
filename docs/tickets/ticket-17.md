## Ticket #17: AGENT-WS-017 — Ontology grounding with existing ChromaDB (`ontology_rag`) and bge-base-en-v1.5 embeddings

You are working in repo `geo-gsm-annotator-agent` (tag: `geo-gsm-annotator-agent-v0.1-llm`).

### Context

There is an existing, separately-built ontology ChromaDB produced by project `rag_ontologies`. We will **consume it read-only**.

* Persistent DB location (directory): `ontology_chroma_db/`
* SQLite file: `ontology_chroma_db/chroma.sqlite3`
* Collection name: `ontology_rag`
* Embeddings: `BAAI/bge-base-en-v1.5` with `normalize_embeddings=True`
* Each document has metadata fields including:

  * `source` (one of the ontology source names below)
  * `term_id`, `label`, `definition`, `synonyms` (list), `ancestors` (list of `{id,label}`)

Ontology sources (exact strings; must be used for filtering):

* Cell Ontology
* Uberon Ontology
* Human Disease Ontology
* Experimental Factor Ontology
* Cellosaurus
* NCI Thesaurus

Example document text format (important: term_id present in metadata and in text):

```
Assay: assay
ID: OBI:0000070
Definition: ...
Synonyms: ...
Ancestors: ...
```

This repo already has:

* grounders under `src/validator/grounders/`
* ontology validation plumbing under `src/validator/ontology_validator.py`, `src/validator/ontology_match.py`
* Chroma client utilities under `src/rag/chroma_client.py`

### Goal

Use the existing ontology ChromaDB (`ontology_rag`) to ground these output fields:

* `tissue_type` -> Uberon Ontology (UBERON)
* `disease` -> Human Disease Ontology (DOID)
* `cell_line` -> Cellosaurus (CVCL)
* `data_type` -> Experimental Factor Ontology (EFO/OBI assay terms)

For each field value (string), retrieve candidates from ChromaDB filtered by `metadata.source`, then deterministically select:

* MATCHED (with `term_id`, `label`, `source`, confidence)
* or return a structured failure state (NO_MATCH / AMBIGUOUS / LOW_CONFIDENCE / INDEX_UNAVAILABLE)

These failures must feed into the existing decision engine so that ontology failures route to LLM repair using `prompts/repair_ontology_guided_v1.txt`.

### Non-goals

* Do not change the 8-field output schema produced by the pipeline.
* Do not rebuild or modify the ontology DB in this repo.
* Do not require internet or remote services.

---

## Implementation tasks

### A) Config additions (agent config + example yaml)

Update:

* `src/agent/config.py`
* `config/example_config.yaml`
* `config/llama3-1b_config.yaml`

Add fields:

```yaml
ontology_chroma_enabled: true
ontology_chroma_db_path: "ontology_chroma_db"          # directory containing chroma.sqlite3
ontology_chroma_collection: "ontology_rag"
ontology_embedding_model_name: "BAAI/bge-base-en-v1.5" # must match DB
ontology_embedding_normalize: true

ontology_top_k: 20

ontology_sources_by_field:
  tissue_type: "Uberon Ontology"
  disease: "Human Disease Ontology"
  cell_line: "Cellosaurus"
  data_type: "Experimental Factor Ontology"

ontology_thresholds:
  min_confidence_to_accept: 0.80
  max_delta_for_ambiguity: 0.05
```

Notes:

* The embedding config must be explicit because retrieval must use the same embedding function as DB.
* Threshold numbers are defaults; keep them configurable.

---

### B) Add a dedicated ontology retrieval module (read-only)

Create a new module:

* `src/rag/ontology_retrieve.py`

Responsibilities:

1. Open persistent Chroma collection `ontology_rag` at `ontology_chroma_db_path`.
2. Ensure embedding function uses:

   * `HuggingFaceEmbeddings(model_name="BAAI/bge-base-en-v1.5", encode_kwargs={"normalize_embeddings": True})`
3. Query top-K by similarity using `query_texts=[query]`
4. Apply `where={"source": <source_name>}` metadata filtering (must be supported by Chroma).
5. Return a structured list of candidates, preserving metadata.

Define a small dataclass (or TypedDict) for candidates:

* `term_id: str` (from metadata.term_id; required when present)
* `label: str` (from metadata.label; required when present)
* `source: str` (from metadata.source)
* `definition: Optional[str]`
* `synonyms: list[str]`
* `ancestors: list[dict]` (keep raw list)
* `distance: float` (or score; whichever Chroma returns)
* `doc_text: str` (optional but useful for audit)

Failure handling:

* If DB path missing, sqlite missing, collection missing, embedding init fails, etc:

  * raise a small internal exception `OntologyIndexUnavailable`
  * caller (validator/grounder) must convert it to a failure code, not crash.

You may reuse/extend `src/rag/chroma_client.py` but keep `ontology_retrieve.py` as the stable API.

---

### C) Deterministic candidate selection (no LLM)

Extend or implement in:

* `src/validator/ontology_match.py`

Add a function:

```python
def choose_best_ontology_candidate(
    raw_value: str,
    candidates: list[OntologyCandidate],
    thresholds: OntologyThresholds,
) -> OntologyMatchResult:
    ...
```

Requirements:

* Normalize `raw_value` and each candidate label/synonyms:

  * lowercase
  * strip punctuation
  * collapse whitespace
* Compute deterministic similarity score `confidence` in [0,1]. Keep it simple and stable:

  1. exact normalized match to label -> 1.0
  2. exact normalized match to any synonym -> 0.98
  3. otherwise use token Jaccard similarity between raw_value and label tokens (and optionally best synonym tokens)

     * `score = max(jaccard(raw,label), max_jaccard(raw,synonyms))`
* Then incorporate retrieval rank as tie-break (not as primary score). Do not use model-dependent floating distances for acceptance thresholds unless you have to.
* Decision:

  * if no candidates -> NO_MATCH
  * if top_score < `min_confidence_to_accept` -> LOW_CONFIDENCE
  * if (top_score - second_score) <= `max_delta_for_ambiguity` and second_score >= min_confidence_to_accept -> AMBIGUOUS
  * else -> MATCHED

Return result including:

* status: MATCHED | NO_MATCH | AMBIGUOUS | LOW_CONFIDENCE
* best: candidate + confidence (when MATCHED)
* alternates: top N (for audit + repair prompt guidance)

---

### D) Integrate into the existing grounders

Update these files to use ontology retrieval + deterministic selection:

* `src/validator/grounders/tissue_type.py` (source = "Uberon Ontology")
* `src/validator/grounders/disease.py` (source = "Human Disease Ontology")
* `src/validator/grounders/cell_line.py` (source = "Cellosaurus")
* `src/validator/grounders/data_type.py` (source = "Experimental Factor Ontology")

Each grounder should:

1. Read config: enabled, db path, collection, top_k, thresholds, sources_by_field
2. Call `retrieve_ontology_candidates(raw_value, source, ...)`
3. Call `choose_best_ontology_candidate(...)`
4. Return a structured object (whatever your current ontology validator expects), at minimum:

   * status
   * matched term_id + label + source (when matched)
   * alternates (top 3-5) for audit
5. If `OntologyIndexUnavailable`, return status INDEX_UNAVAILABLE.

Important:

* Use metadata.term_id and metadata.label directly (do not rely on regex parsing unless metadata missing).
* Do not change the outer pipeline annotation schema.

---

### E) Ontology validator and failure codes

Update:

* `src/validator/failure_codes.py`
* `src/validator/ontology_validator.py`

Add failure codes (exact naming is flexible but keep consistent):

* `ONTOLOGY_INDEX_UNAVAILABLE`
* `ONTOLOGY_NO_MATCH_TISSUE_TYPE`
* `ONTOLOGY_AMBIGUOUS_TISSUE_TYPE`
* `ONTOLOGY_LOW_CONFIDENCE_TISSUE_TYPE`
  (similarly for DISEASE, CELL_LINE, DATA_TYPE)

Ontology validator should:

* run grounding for each applicable field
* emit failure codes based on match result status
* attach compact grounding info to audit:

  * best term_id/label/source/confidence
  * alternates (term_id/label/confidence) top 3
* keep logs bounded (no huge ancestor dumps)

---

### F) Decision routing to existing repair prompt

Update `spec/decision_table.yaml`:

* Route `ONTOLOGY_NO_MATCH_*` and `ONTOLOGY_AMBIGUOUS_*` to REPAIR using `prompts/repair_ontology_guided_v1.txt`
* Route `ONTOLOGY_LOW_CONFIDENCE_*` to REPAIR (recommended default)
* Route `ONTOLOGY_INDEX_UNAVAILABLE` to ACCEPT_WITH_FLAG (default) so pipeline still runs when DB missing

Do not change the decision engine design; only add mappings.

---

### G) Tests

Add: `tests/test_ontology_chroma_grounding.py`

1. Unit tests with stubs (default)

* Monkeypatch `retrieve_ontology_candidates` to return small candidate sets.
* Verify:

  * exact label match -> MATCHED
  * synonym match -> MATCHED
  * close tie -> AMBIGUOUS
  * low similarity -> LOW_CONFIDENCE
  * empty -> NO_MATCH

2. Optional integration test (skipped unless env var set)

* If `ONTOLOGY_DB_PATH` is present and points to a real `ontology_chroma_db`, run:

  * query “PBMC” against Cell Ontology or Uberon (choose one consistent with your expectations)
  * assert retrieval returns candidates and selector produces deterministic output
    Keep it tolerant: assert “non-empty candidates” rather than a hard-coded ID unless you have a known stable term in the DB.

---

### H) Minimal docs update

Update `docs/RESUME.md` (or `README.md`) with:

* how to place `ontology_chroma_db/` next to the repo
* how to enable grounding in config
* embedding model requirement: `BAAI/bge-base-en-v1.5` normalize embeddings

---

## Acceptance criteria

* `uv run pytest -q` passes.
* With `ontology_chroma_enabled=true` and `ontology_chroma_db/` present:

  * grounders retrieve using Chroma filtered by the correct `metadata.source`
  * ontology validator emits no false crashes; only controlled failures
* With DB absent:

  * pipeline runs and emits `ONTOLOGY_INDEX_UNAVAILABLE` (and routes per decision table)
* No changes to the 8-field output schema.

---

## Notes for implementation

* Be careful to instantiate the same embedding function used to build the DB:

  * `BAAI/bge-base-en-v1.5` + normalized embeddings
* Prefer using metadata keys:

  * `term_id`, `label`, `synonyms`, `definition`, `source`
* Keep selection logic deterministic and unit-testable.

---