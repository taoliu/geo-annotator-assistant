# Checkpoint — 2026-01-09 (Post v0.6)

## Purpose

This checkpoint captures the **authoritative system state after milestone v0.6** and is intended as a **handoff and reset anchor** for starting a new development session.

It summarizes what is stable, what is allowed to change next, and what must not be revisited without explicit approval.

---

## Current System State (Authoritative)

### Backend

* Backend pipeline is **stable, deterministic, and complete** through v0.6.
* Core pipeline ordering, decision routing, and output schema are unchanged.
* All v0.6 changes are robustness and performance improvements, not redesigns.

### Output Contract

* Final output schema is fixed at **8 fields**:

  * `gse_accession`
  * `gsm_accession`
  * `data_type`
  * `organism`
  * `tissue_type`
  * `cell_line`
  * `disease`
  * `treatment`
* No ontology IDs appear in final outputs.
* Any additional metadata is recorded only in audit artifacts.

---

## Ontology Grounding Behavior (v0.6)

### Deterministic-first retrieval

* Ontology retrieval prioritizes **exact metadata and ID matches**.
* Approximate vector search is **fallback-only**.
* Exact matches short-circuit retrieval and embedding calls.

### Terminal exact matches

A terminal exact match is defined as:

* `status == MATCHED`
* `score == 1.0`
* exact match type (label, normalized label, synonym, or ID)

Terminal exact matches:

* stop further retrieval
* avoid embeddings
* may trigger canonicalization and locking

### Canonicalization and locking

* For terminal exact matches, output values may be deterministically
  canonicalized to ontology labels.
* Canonicalization and locking are **config-gated**.
* Locked fields are protected from later repair overwrites.

### Disease ontology strategy

* Human Disease Ontology (DOID) is the primary source.
* NCIT is used as a **secondary fallback** only when:

  * DOID is not terminal exact, and
  * the disease label triggers a malignant-neoplasm lexical rule.
* Trigger terms are configurable.
* Selection between DOID and NCIT is deterministic and auditable.

---

## Validation and Repair Model

* Validation classes and decision routing are unchanged.
* Repairs remain field-scoped and bounded.
* Locked fields (from ontology terminal exact matches) are not repair targets.
* Repair loops and fallback behavior are deterministic.

---

## Performance Characteristics

* Major speedup achieved by eliminating unnecessary embedding calls.
* Vector search is now rare and intentional.
* Embedding device (`cpu`, `cuda`, `mps`) is explicitly configurable.
* GSE-scale runs are feasible on a single accelerator.

---

## Configuration Notes

* Ontology and retrieval configuration lives under:

  * `rag.*`
  * `rag.ontology.*`
* Canonicalization, locking, and NCIT fallback are config-gated.
* No learning or persistence is enabled.

---

## What Is Locked

The following should not be revisited in the next milestone without explicit approval:

* Core pipeline ordering
* 8-field output schema
* Deterministic decision routing
* Ontology grounding semantics
* Repair loop structure

---

## What Is Open for Next Milestone (v0.7)

* Curator UI design and usability
* Visualization of grounding evidence
* Override ergonomics
* Non-semantic UI refinements

Backend semantics introduced in v0.6 are considered **stable and frozen**.

---

## How to Resume Work

To start a new session:

1. Read `docs/whitepaper.md` (architectural law)
2. Read `docs/milestones/v0.6-rag-validation.md`
3. Use this checkpoint as the current truth
4. Propose new work only via tickets, scoped to UI unless otherwise approved

---

**Checkpoint status:** ARCHIVED
