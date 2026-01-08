# GEO GSM Annotator Agent — Project Resume

This document summarizes the **current state, guarantees, and operating assumptions**
of the project.

It is intended to help **new contributors and new AI coding sessions**
resume work safely, correctly, and without violating architectural invariants.

---

## Project Status

* **Current milestone**: **v0.5 — Curator UI and Review Workflow**
* **Stability level**: backend-stable, UI-functional
* **Intended users**: computational biologists, data curators
* **Primary use**: GSM-level metadata normalization, review, and explicit correction

The backend reached stability in v0.4.
v0.5 completes the human review loop without altering backend behavior.

---

## What Exists and Works

### Core Pipeline (Backend, v0.4-stable)

* Deterministic end-to-end pipeline:
  * context ingestion
  * LLM proposal generation
  * format validation
  * semantic validation
  * ontology grounding
  * decision routing
  * bounded repair loop
  * final decision
* Strict execution ordering enforced
* Fully wired for GSM-level and GSE-level processing
* No hidden or persistent state between runs

### Performance

* **Single-GPU, single-process model reuse**
  * Local HuggingFace LLM loaded once per run
  * All GSMs reuse the same model instance
  * No change to inference semantics or outputs
* GSE-scale processing is practical on a single GPU

---

## Outputs and Review Artifacts

A standard run may produce:

* `curation.tsv`  
  Curator-friendly tabular summary

* `curation.jsonl`  
  Lossless JSON mirror of `curation.tsv` using native JSON types

* `evidence.jsonl`  
  Structural diagnostic evidence per GSM and per field, derived strictly from audits:
  * repair attempt counts
  * terminal fallback usage
  * ontology grounding status
  * field-level flags  
  No free-text rationale, no new inference

* `suggestions.jsonl` (optional)  
  Advisory, cross-GSM diagnostics:
  * majority outliers
  * singleton values  
  Suggestions never modify outputs

* `audit.jsonl`  
  Mandatory, structured audit log capturing all decisions and provenance

---

## Repair and Validation Guarantees

* Field-scoped repairs only
* Per-field attempt limits
* Global repair cap
* Terminal fallback values respected
* Anti-cycling constraint enforced
* Evidence-first failure prioritization

---

## Ontology Integration

* Read-only ontology usage
* Deterministic grounding thresholds
* Grounding influences decisions but does not directly mutate outputs
* Clear separation between semantic validation and ontology grounding

---

## GSE-Level Processing

* GSE accession ingestion (SOFT or JSONL)
* Independent GSM decisions
* GSE-level diagnostics and reporting
* **No forced label propagation across GSMs**

---

## Human-in-the-Loop Curation

### Override Mechanism (Backend Contract)

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
* All applied overrides are recorded in audit logs with old/new values

This makes human intervention explicit, deterministic, and auditable.

### Curator UI (v0.5)

* Local, Streamlit-based curator UI
* Read-only by default
* Loads:
  * `curation.jsonl`
  * `evidence.jsonl`
  * `suggestions.jsonl` (optional)
* Wide, searchable GSM table
* Per-GSM detail panels showing raw artifacts
* Evidence-derived field-level issue highlighting
* Explicit edit mode:
  * inline table editing of canonical fields
  * edits are session-scoped (in-memory only)
* Deterministic export of `overrides.jsonl`
  * backend-compatible schema
  * preview-before-export
  * no automatic writes

The UI introduces **no persistence, no learning, and no inference**.

---

## What Is Explicitly Not Present

The following are **intentional design exclusions**, not missing features:

* Persistent or collaborative curation state
* Automatic application of suggestions
* Learning or adaptation from human edits
* Forced cross-GSM consensus or voting
* Ontology validation of override values

Any introduction of these requires a new milestone and explicit documentation.

---

## Invariants (Do Not Break)

The following must remain true across v0.x:

* Output schema: **exactly 8 canonical fields**
* Deterministic decision engine
* Mandatory audit emission
* Ontology grounding is read-only
* No silent or unbounded repair loops
* No hidden or persistent state
* GSM independence is preserved

Violating any invariant requires:
* design discussion
* milestone update
* explicit documentation

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

## Current Direction

* v0.5 curator UI is complete
* Backend remains v0.4-stable and unchanged
* Next milestone is expected to focus on:
  * validation logic refinement
  * LLM transport abstraction (llama.cpp, OpenAI-style HTTP)
  * deployment and performance optimization
