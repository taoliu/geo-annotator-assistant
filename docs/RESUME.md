# GEO GSM Annotator Agent — Project RESUME

## Project Overview

**GEO GSM Annotator Agent** is a deterministic, audit-first system for annotating and standardizing GEO sample-level (GSM) metadata.

It combines large language models for proposal generation with strict deterministic validation, ontology grounding, and bounded repair loops, followed by explicit human override.

The system is designed for correctness, transparency, and curator trust, not end-to-end automation.

---

## Problem Addressed

GEO GSM metadata is:

* heterogeneous and inconsistently labeled
* partially free-text
* often ambiguous or incomplete

Purely rule-based systems fail to generalize, while unconstrained LLM systems hallucinate.

This project bridges the gap by separating:

* **proposal generation** (LLMs)
* **decision making** (deterministic logic)
* **normalization and confidence assessment** (ontologies)
* **final judgment** (human curator)

---

## Core Capabilities

### Deterministic Annotation Pipeline

* Exactly **8 output fields** per GSM:

  * `gse_accession`
  * `gsm_accession`
  * `data_type`
  * `organism`
  * `tissue_type`
  * `cell_line`
  * `disease`
  * `treatment`
* Fixed pipeline ordering
* Deterministic decision routing
* Bounded, field-scoped repair loops

---

### Ontology Grounding (Validation-Only)

* Read-only ontologies
* Deterministic matching
* Canonicalization for terminal exact matches
* Ambiguous and no-match cases surfaced explicitly
* Ontology confidence does not imply correctness

---

### Retrieval-Augmented Generation (RAG)

* Deterministic and auditable
* Read-only
* Fallback-only
* Never decisive

---

### Audit and Diagnostics

* Structured audit artifacts for every GSM
* No free-text rationale
* Fully explainable decisions

---

### Human-in-the-Loop Overrides

* Curator overrides are first-class inputs
* Overrides are explicit and session-only
* Overrides do not retrigger backend logic
* Full diff and revert support in UI

---

## Curator UI (v0.7)

* Table-first interface for large GSEs
* Modal-based GSM detail inspection
* Field status dashboard (locked, canonicalized, ambiguous, overridden)
* Structured evidence panels
* Safe override ergonomics
* Table-level triage and filters

UI is strictly non-authoritative and never alters backend semantics.

---

## Architectural Invariants

The following are treated as law:

* 8-field output schema
* Deterministic decision routing
* Ontology grounding as validation only
* RAG as fallback-only
* No persistence or learning
* Explicit auditability

These invariants are defined in `docs/whitepaper.md`.

---

## Current Status

* Backend stable and frozen after v0.6
* Curator UI refined and closed in v0.7
* Ready for end-to-end robustness review and incremental fixes

---

## Intended Users

* Bioinformatics curators
* Data integration teams
* AI-assisted curation pipelines

---

## Non-Goals

* Fully autonomous annotation
* Learning from human edits
* Schema expansion
* Ontology mutation

---

## Development Model

* All work is ticketed
* Milestones define medium-term state
* Whitepaper defines architectural law
* Checkpoints define session reset anchors

---

## Repository Entry Points

* Backend CLI: `geo-gsm-annotate`
* Curator UI: `geo-gsm-ui`

---

## Summary

The GEO GSM Annotator Agent prioritizes **correctness, determinism, and trust** over automation.

It is designed to scale across datasets while remaining auditable, explainable, and human-governed.
