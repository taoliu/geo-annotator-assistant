# GEO GSM Annotator Agent — Project Resume

This document summarizes the **current state, guarantees, and operating assumptions** of the project.
It is intended to help **new contributors and new AI coding sessions** resume work safely and correctly.

---

## Project Status

* **Current milestone**: **v0.4 — Curator-Ready Backend**
* **Stability level**: backend-stable
* **Intended users**: computational biologists, data curators
* **Primary use**: GSM-level metadata normalization, review, and correction

v0.4 closes the backend phase of development. No UI is included yet.

---

## What Exists and Works (v0.4)

### Core Pipeline

* Deterministic end-to-end pipeline:

  * context ingestion
  * LLM generation (proposal only)
  * format validation
  * semantic validation
  * ontology grounding
  * decision routing
  * bounded repair loop
  * final decision
* Fully wired across GSM and GSE modes
* Strict execution ordering enforced
* No hidden state between runs

### Performance

* **Single-GPU, single-process model reuse**

  * Local HuggingFace LLM is loaded once per run
  * All GSMs reuse the same model instance
  * No change to inference semantics or outputs
* GSE-scale processing is practical on one GPU

---

### Outputs and Review Artifacts

A typical v0.4 run may produce:

* `curation.tsv`
  Curator-friendly tabular summary (unchanged semantics from v0.3)

* `curation.jsonl`
  Lossless JSON mirror of `curation.tsv` using native JSON types

* `evidence.jsonl`
  Structural diagnostic evidence per GSM and per field, derived only from audits:

  * repair attempt counts
  * terminal fallback usage
  * ontology grounding status
  * field-relevant flags
    No free-text rationale, no new inference

* `suggestions.jsonl` (opt-in)
  Advisory cross-GSM diagnostics:

  * majority outliers
  * singleton values
    Suggestions never modify outputs

* `audit.jsonl`
  Mandatory, structured audit log capturing all decisions and provenance

---

### Repair and Validation

* Field-scoped repairs only
* Per-field attempt limits
* Global repair cap
* Terminal fallback values respected
* Anti-cycling constraint enforced
* Evidence-first failure prioritization

---

### Ontology Integration

* Read-only ontology usage
* Deterministic grounding thresholds
* Grounding influences decisions but does not directly mutate outputs
* Clear separation from semantic validation

---

### GSE-Level Processing

* GSE accession ingestion (SOFT or JSONL)
* Independent GSM decisions
* GSE-level diagnostics and reporting
* **No forced label propagation across GSMs**

---

### Human-in-the-Loop Curation (v0.4)

* Human corrections are expressed **only** via an explicit input artifact:

  * `overrides.jsonl`
* Each override targets:

  * one GSM
  * one canonical output field
  * a new value
* Overrides:

  * are optional
  * apply after automated inference and repair
  * do not trigger re-inference or re-grounding
* All applied overrides are recorded in audit logs with old/new values and optional metadata

This makes human intervention explicit, deterministic, and auditable.

---

## What Is Explicitly Deferred

The following are **intentional deferrals**, not missing features:

* Curator UI (web or desktop)
* Persistent or collaborative curation state
* Learning or adaptation from human edits
* Forced cross-GSM consensus or voting
* Ontology validation of override values

These are planned for **v0.5+**.

---

## Invariants (Do Not Break)

The following must remain true across v0.x:

* Output schema: **exactly 8 canonical fields**
* Deterministic decision engine
* Mandatory audit emission
* Ontology grounding is read-only
* No silent repair loops
* No hidden or persistent state
* GSM independence is preserved

Any change that violates these invariants requires:

* a design discussion,
* a milestone update,
* and explicit documentation.

---

## How Work Is Organized

* **Whitepaper** (`docs/whitepaper.md`)
  Long-term architectural law

* **Milestones** (`docs/milestones/`)
  Medium-term state snapshots

* **Checkpoints** (`docs/checkpoints/`)
  Operational memory and handoff points

* **Tickets** (`docs/tickets/`)
  Short-term, executable work units

All code changes must correspond to a ticket.

---

## Guidance for New AI / Codex Sessions

Before coding:

1. Read:

   * `docs/whitepaper.md`
   * the latest milestone doc
   * the latest checkpoint doc
2. Identify the active ticket number.
3. Do **not** redesign architecture unless explicitly instructed.
4. Prefer incremental, testable changes.
5. Record the active ticket in the Codex session notes.

---

## Current Next Direction

* v0.4 backend is complete and stable
* Begin **v0.5** planning:

  * curator UI
  * review and override interfaces
  * visualization of evidence and suggestions

Backend redesign is **not** expected in v0.5.

---
