# GEO GSM Metadata Annotator Agent
## Project White Paper

---

## 1. Motivation

GEO (Gene Expression Omnibus) contains millions of samples (GSMs) with rich but
**heterogeneous and inconsistently structured metadata**. This limits:
- large-scale meta-analysis
- cross-study integration
- automated dataset discovery
- downstream machine learning

Manual curation does not scale. Pure LLM-based annotation is powerful but unsafe
without grounding and validation.

This project builds a **hybrid AI agent** that combines:
- LLM inference
- biomedical ontologies
- deterministic validation
- human-in-the-loop review

---

## 2. Scope

### Input
- GSM accession number
- GSM metadata (SOFT format)
- Parent GSE metadata

### Output
A standardized GSM annotation with fixed fields:

| Field | Description |
|------|------------|
| data_type | Assay / technology |
| organism | Species |
| tissue_type | Anatomical tissue |
| cell_line | Immortalized cell line or `No` |
| disease | Disease or `Healthy` |
| treatment | Experimental intervention |

Each output is accompanied by a full **audit record**.

---

## 3. High-Level Architecture

1. **Fetcher / Parser**
   - Downloads GSM SOFT
   - Extracts GSM + GSE context
   - Produces JSONL text for LLM

2. **LLM Label Proposal**
   - Fine-tuned model
   - Produces strict JSON output
   - No ontology knowledge assumed

3. **Validation & Grounding**
   - Format validation
   - Semantic heuristics
   - Cross-field consistency checks
   - Ontology grounding (RAG via ChromaDB)

4. **Decision & Repair**
   - Decision table maps failures → actions
   - Bounded repair attempts
   - Conservative fallbacks
   - Escalation to human review

5. **Outputs**
   - annotations.jsonl
   - audit.jsonl
   - flagged.jsonl

---

## 4. Ontology Strategy

Controlled vocabularies are enforced via ontology grounding:

| Field | Ontology |
|------|---------|
| data_type | EFO (assay branch) |
| tissue_type | UBERON |
| cell_line | Cellosaurus |
| disease | NCIt (malignant neoplasm subset), DOID fallback |

Grounding uses:
- Local ChromaDB (vector + metadata)
- Deterministic thresholds
- Explicit fallback rules

---

## 5. Validation Philosophy

### Key principles
- Never trust raw LLM output
- Prefer `Unknown` / `No` / `Healthy` over hallucination
- Escalate ambiguity rather than guessing
- Keep logic transparent and auditable

### Validation layers
1. Format (JSON, keys, word limits)
2. Semantic (cell vs tissue, treatment leakage)
3. Consistency (assay vs platform, disease vs context)
4. Ontology grounding (score thresholds)

---

## 6. Human-in-the-Loop Design

The system explicitly supports human review:
- Ambiguous samples are written to `flagged.jsonl`
- Audit records explain *why* a sample was flagged
- Future work will support curator overrides

This ensures:
- traceability
- continuous improvement
- trust in downstream analyses

---

## 7. Implementation Status

As of 2026-01-02:
- Full walking skeleton implemented
- All logic tested (49 unit tests)
- Parser, LLM, and ontology grounders are stubbed
- Ready for real-world integration

---

## 8. Future Directions

- Full-scale GSM batch processing
- Active learning from human corrections
- Confidence scoring per field
- Integration with GEO search and downstream pipelines

---

## 9. Guiding Principle

**LLMs propose. Ontologies ground. Rules decide. Humans arbitrate.**
