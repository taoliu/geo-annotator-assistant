# Checkpoint — 2026-01-05

## Project
**geo-gsm-annotator-agent**

## Milestone status
- **v0.2: COMPLETED**
- Repository tagged: `geo-gsm-annotator-agent-v0.2`

This checkpoint marks the end of milestone v0.2 and the transition to milestone v0.3.

---

## Summary of work completed since last checkpoint (2026-01-02)

### 1. Repair loop fully wired into pipeline
- `apply_repairs()` was implemented earlier but never invoked.
- The repair loop is now correctly wired into **all CLI execution paths**:
  - `--gsm`
  - `--gsm-file`
  - `--jsonl`
  - `--gse`
- Repair actions (REPAIR / FALLBACK / ESCALATE) now affect `final_output` and `final_decision`.

### 2. Ontology grounding via ChromaDB stabilized
- Local ChromaDB (`ontology_chroma_db`) integrated and functional.
- Correct handling of:
  - embedding conflicts
  - query API changes (removed invalid `include=["ids"]`)
  - exact label lookups using `collection.get(where={"$and": [...]})`
- Retrieval verified for DOID, EFO, Uberon, Cellosaurus.

### 3. Synonym-aware ontology matching
- Ontology matching enhanced to support:
  - exact label matches
  - exact synonym matches (e.g. `CLL` → `chronic lymphocytic leukemia`)
- Audit fields added:
  - `match_type` (`label_exact`, `synonym_exact`, `jaccard`)
  - `matched_via` (`label` / `synonym`)
  - `matched_synonym`
- Fixed synonym ingestion bug where synonym lists were stored as single strings.

### 4. Evidence-first repair policy implemented
- New short-circuit rule:
  - `*_inferred_without_evidence` failures are handled **before** ontology confidence failures.
- This prevents ontology matches from overriding lack-of-evidence conditions.

### 5. Cell line vs cell type semantic separation
- Introduced semantic failure:
  - `cell_line_is_cell_type`
- Cell types (e.g. `CD8+ T cells`, `CD45+ tumor infiltrating cells`) are no longer forced through Cellosaurus.
- Correct behavior:
  - semantic error raised
  - ontology grounding skipped
  - fallback applied (`cell_line = "No"`)

### 6. Decision engine and fallback behavior corrected
- Semantic errors are now included in `failures_by_field`.
- FALLBACK actions correctly update `state.final_output`.
- Repair history reflects actual actions taken.

### 7. Data type and disease improvements
- Data type:
  - synonym-aware matching works (e.g. `scRNA-seq`)
  - some EFO retrieval gaps (e.g. `ATAC-seq`) identified for future work
- Disease:
  - synonym ambiguity resolved deterministically
  - `CLL` now correctly resolves to DOID:1040
  - ambiguous synonym collisions handled via policy

---

## Known limitations (intentionally deferred to v0.3)

1. **Tissue type = lesion problem**
   - Terms like `tumor` are not anatomical entities in Uberon.
   - Current behavior: LOW_CONFIDENCE + repair attempts.
   - Planned fix: lesion-aware tissue policy and context-based anatomy extraction.

2. **Confidence calibration**
   - Confidence scores for synonym matches are currently uniform (1.0).
   - More nuanced confidence modeling may be needed with real data.

3. **ATAC-seq retrieval gap**
   - EFO:0007045 exists but does not rank in top-k retrieval.
   - Requires investigation of embedding space and/or hybrid exact-first retrieval.

---

## Validation status
- All unit tests passing:

**Checkpoint status:** ARCHIVED
