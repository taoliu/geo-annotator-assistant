# GEO GSM Metadata Annotation Agent — Whitepaper

## Overview

This project implements a modular, auditable system for annotating
GEO GSM samples with structured biological metadata using
large language models (LLMs) and controlled vocabularies.

The primary goal is to extract concise, standardized labels
(e.g. assay type, tissue, disease) from heterogeneous GEO metadata
while preserving reproducibility, transparency, and scientific rigor.

---

## System Design Principles

The system is designed around the following core principles:

1. **Separation of concerns**
2. **Strict output contracts**
3. **Repair over rejection**
4. **Audit-first execution**
5. **Ontology compatibility**

These principles guide all architectural decisions.

---

## High-Level Architecture

The pipeline is composed of four logically independent stages:

1. **Ingestion**
2. **LLM-based reasoning**
3. **Validation and repair**
4. **Output curation and auditing**

Each stage can evolve independently.

---

## Ingestion Layer

The ingestion layer is responsible for:
- Downloading GEO SOFT files
- Parsing GSM- and GSE-level metadata
- Producing a per-GSM textual context

The output of ingestion is a JSONL file where each record contains:
- `context_text` (human-readable evidence)
- `gsm_accession`
- `gse_accession`

Ingestion **does not** define prompts or schemas and does not
perform reasoning.

---

## LLM-Based Annotation Engine

The annotation engine uses an instruction-tuned LLM to infer
structured labels from the GSM context text.

Key properties:

- **Local in-process inference**
  - Models are loaded directly from local weights
  - No external API or HTTP server is required
  - Suitable for restricted environments (HPC, secured servers)

- **Chat-template prompting**
  - Prompts are rendered using the tokenizer’s native chat template
  - Improves instruction adherence and output consistency

- **Fixed schema contract**
  - The model must return exactly eight fields:
    - `gse_accession`
    - `gsm_accession`
    - `data_type`
    - `organism`
    - `tissue_type`
    - `cell_line`
    - `disease`
    - `treatment`

---

## Validation Layer

All model outputs are validated deterministically.

Validation includes:
- JSON parseability
- Exact key matching
- Word-length constraints
- Basic semantic consistency checks
- Cross-field consistency checks

The system is intentionally strict about schema correctness.

---

## Robust Output Parsing

LLMs frequently emit:
- Markdown code fences
- Explanatory text
- Mixed formatting

The validator therefore extracts the **first valid JSON object**
from the model output before validation.

This improves robustness without weakening schema enforcement.

---

## Repair Loops

Rather than rejecting invalid outputs, the system attempts repair.

Two repair mechanisms exist:

### Format Repair
Triggered when schema or formatting rules fail.
The model is re-prompted to correct formatting errors.

### Decision-Based Repair
Triggered by semantic or consistency failures.
A decision table governs:
- Whether to repair
- Which field to target
- How many attempts are allowed
- When to fall back or escalate

Repairs always return the **full schema**, simplifying validation
and merge logic.

---

## Decision Engine

All non-trivial failures are routed through a decision table.

Each failure type maps to:
- an action (REPAIR, FALLBACK, ESCALATE)
- a target field
- retry limits
- severity level

This makes system behavior explicit, testable, and extensible.

---

## Audit and Reproducibility

Every GSM annotation produces a complete audit record containing:
- Prompt and validator versions
- All raw LLM outputs (initial + repairs)
- Parsed outputs
- Validation results
- Repair history
- Final decision and output

This enables full reproducibility and post-hoc analysis.

---

## Controlled Vocabulary Alignment (Planned)

The system is designed to integrate ontology grounding
(e.g. EFO, UBERON, DOID, Cellosaurus, NCIT).

Ontology alignment is treated as a validation and repair stage,
not as a post-processing step.

---

## Summary

This architecture allows the system to leverage LLM reasoning
while maintaining strong guarantees required for scientific
metadata curation.

The design favors transparency, extensibility, and correctness
over raw throughput.
