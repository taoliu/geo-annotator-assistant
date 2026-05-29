# GEO GSM Annotator Agent — Project Snapshot

## Purpose

**GEO GSM Annotator Agent** is a deterministic, audit-first system for annotating and standardizing GEO sample-level (GSM) metadata with explicit human-in-the-loop curation.

The system prioritizes correctness, transparency, and reproducibility over automation.

---

## Current Status

* Backend semantics stabilized and consolidated through **v1.4**
* Curator web UI production-ready as of **v1.1**
* CLI ergonomics, batch safety, and ingest robustness completed in **v1.2**
* Web UI refinement completed in **v1.3**
* Backend determinism and real-world edge-case normalization consolidated in **v1.4**
* Validation, repair, ontology grounding, and reporting behavior explicitly governed by policy
* Real-world GEO edge cases handled deterministically with reduced false flags

---

## Core Capabilities

* Deterministic annotation pipeline producing **exactly 8 GSM fields**:

  * `gse_accession`
  * `gsm_accession`
  * `data_type`
  * `organism`
  * `tissue_type`
  * `cell_line`
  * `disease`
  * `treatment`

* Policy-governed validation and bounded repair loops

* Deterministic decision routing via explicit decision table

* Ontology grounding used strictly for validation and confidence assessment

* Deterministic canonicalization layer preceding ontology grounding

* Unified placeholder model:

  * `"Healthy"` for biological healthy state
  * `"Unknown"` for missing or unspecified values

* Structured audit artifacts for every GSM

* Explicit and replayable curator overrides

* Codex-assisted read-only investigation workflow for architectural debugging

---

## Deterministic Normalization (v1.4 Highlights)

* Composite tissue resolution with all-components-required rule
* Cross-ontology synonym parsing standardized
* "Not Available" mapped to canonical `"Unknown"`
* Compound healthy strings normalized to `"Healthy"`
* Deterministic disease rewrites (e.g., mesothelioma → NCIT malignant mesothelioma)
* Structured organism context authority enforced (no free-text conflict scanning)
* Reduced unnecessary ontology repair loops

---

## Intended Workflow

1. Prepare a YAML configuration
2. Run `gaa-annotate` on GSE(s)
3. Review and curate results via the web UI
4. Export final CSVs using `gaa-summarize` or via web UI export

---

## Architectural Invariants

Treated as law:

* Fixed 8-field output schema
* Deterministic pipeline ordering
* LLM proposes, deterministic logic decides
* No learning from curator edits
* RAG as fallback only
* Ontologies as validation only
* Canonicalization precedes grounding
* Structured context overrides free text
* Full auditability and replayability
* Human curator as final authority

Defined in `docs/whitepaper.md`.

---

## Intended Users

* Bioinformatics curators
* Data integration teams
* AI-assisted curation pipelines requiring auditability and reproducibility

---

## Repository Entry Points

* Agent CLI: `gaa-annotate`
* Post-curation export CLI: `gaa-summarize`
* Curator UI: `gaa-ui`

---
