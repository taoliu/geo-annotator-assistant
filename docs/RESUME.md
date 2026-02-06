# GEO GSM Annotator Agent — Project RESUME

## Project Overview

**GEO GSM Annotator Agent** is a deterministic, audit-first system for annotating and
standardizing GEO sample-level (GSM) metadata.

It combines large language models for proposal generation with strict deterministic
validation, ontology grounding, and bounded repair loops, followed by explicit human
curator judgment.

The system is designed for correctness, transparency, and curator trust, not end-to-end
automation.

---

## Problem Addressed

GEO GSM metadata is:

- heterogeneous and inconsistently labeled
- partially free-text
- often ambiguous, underspecified, or sloppy

Purely rule-based systems fail to generalize, while unconstrained LLM systems hallucinate
or over-normalize.

This project bridges the gap by **separating responsibilities**:

- proposal generation → LLMs
- decision making → deterministic logic
- normalization & confidence assessment → ontologies
- final judgment → human curators

---

## Core Capabilities

### Deterministic Annotation Pipeline

- Exactly **8 output fields** per GSM:
  - `gse_accession`
  - `gsm_accession`
  - `data_type`
  - `organism`
  - `tissue_type`
  - `cell_line`
  - `disease`
  - `treatment`
- Fixed pipeline ordering
- Deterministic decision routing
- Field-scoped, bounded repair loops
- Explicit terminal vs non-terminal outcomes

---

### Ontology Grounding (Validation-Only)

- Read-only ontologies (EFO, UBERON, DOID, NCIT, Cellosaurus)
- Deterministic matching and scoring
- Canonicalization only for terminal exact matches
- Ambiguous, low-confidence, and no-match cases surfaced explicitly
- Ontology confidence does **not** imply semantic correctness

---

### Retrieval-Augmented Generation (RAG)

- Deterministic and auditable
- Read-only
- Fallback-only
- Never decisive
- Cannot override deterministic validation

---

### Validation, Repair, and Policy Layer (v0.9)

- Explicit validation rules for real-world GEO metadata
- Deterministic repair triggering boundaries
- Clear distinction between:
  - acceptable outputs
  - flaggable outputs
  - repairable failures
- Non-anatomical tissue placeholders handled explicitly
- Disease generalization applied conservatively and deterministically
- Unknown or underspecified values handled via documented fallback rules

All rules are documented in `docs/policies/policy-spec.md`.

---

### Audit and Diagnostics

- Structured audit artifact generated for every GSM
- Machine-readable failure codes and flags
- No free-text rationale
- Fully explainable and replayable decisions
- Clear separation of flags vs fatal failures

---

### Human-in-the-Loop Overrides

- Curator overrides are first-class inputs
- Overrides are explicit and persisted per GSE
- Overrides never retrigger backend logic
- Full diff visibility and revert support
- Backend semantics remain unchanged

---

## Curator UI (v1.1)

The curator interface is production-ready for large-scale, real-world curation.

Key features:

- AG Grid–based curation table with always-on editing
- Pinned, icon-based workflow columns:
  - Status (row state)
  - Checked (persistent curator review marker)
  - Edited (live pencil indicator)
- Evidence-driven transparency:
  - all per-field diagnostics sourced exclusively from `evidence.jsonl`
  - field-level hover tooltips for detailed inspection
  - fallback states shown as informational, not warnings
- Removal of redundant diagnostic columns and modal-based inspection
- Explicit bulk editing:
  - multi-row selection
  - single-column, single-value apply
  - preview before apply
  - full reversibility
- Progressive disclosure for destructive actions
- Reporting-ready exports:
  - per-GSE CSV
  - aggregate CSV across all GSEs loaded via `--input-dir`

The UI is strictly non-authoritative and never alters backend semantics.

---

## Architectural Invariants

The following are treated as **law**:

- Fixed 8-field output schema
- Deterministic decision routing
- Ontology grounding as validation only
- RAG as fallback only
- No learning from curator edits
- Explicit auditability
- Human curator as final authority

These invariants are defined in `docs/whitepaper.md`.

---

## Current Status

- Backend stable and policy-hardened through **v0.9**
- Curator UI refined and production-ready as of **v1.1**
- Validation, repair, and reporting behavior consolidated
- Policy layer fully documented
- Real-world GEO edge cases handled deterministically
- Canonical output defined as `annotations.jsonl`
- All ambiguity surfaced via explicit flags, never hidden heuristics

---

## Intended Users

- Bioinformatics curators
- Data integration teams
- AI-assisted curation pipelines requiring auditability and reproducibility

---

## Non-Goals

- Fully autonomous annotation
- Learning from curator edits
- Schema expansion
- Ontology mutation
- Cross-dataset inference

---

## Development Model

- All work is ticket-driven
- Tickets reference policy when applicable
- Milestones define medium-term state
- Whitepaper defines architectural law
- Policies define allowed behavior
- Checkpoints define session reset anchors

---

## Repository Entry Points

- Backend CLI: `geo-gsm-annotate`
- Curator UI: `geo-gsm-ui`

---

## Summary

The GEO GSM Annotator Agent prioritizes **correctness, determinism, and curator trust**
over automation.

By making policy explicit and behavior auditable, the system scales across messy
real-world GEO metadata while remaining explainable, reproducible, and human-governed.
