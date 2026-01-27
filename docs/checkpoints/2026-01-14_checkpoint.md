# Checkpoint — 2026-01-14 (Post v0.7)

## Purpose

This checkpoint captures the **authoritative project state after milestone v0.7** and serves as a clean reset anchor for starting the next development milestone.

It records what is stable, what is frozen, and what is open for change, so a new session can resume work without revisiting settled decisions.

---

## Current System State (Authoritative)

### Backend

* Backend pipeline is **stable, deterministic, and frozen** as of v0.6.
* No backend changes were made during v0.7.
* Pipeline ordering, decision routing, and repair semantics remain unchanged.

### Output Contract

* Final output schema is fixed at **exactly 8 fields** per GSM:

  * `gse_accession`
  * `gsm_accession`
  * `data_type`
  * `organism`
  * `tissue_type`
  * `cell_line`
  * `disease`
  * `treatment`

* No ontology IDs appear in final outputs.

* All auxiliary information exists only in audit artifacts.

---

## Ontology Grounding Behavior (Frozen)

* Ontology grounding is **validation and normalization only**.
* Deterministic-first retrieval is enforced:

  * exact matches before approximate or vector search
  * vector search is fallback-only
* Terminal exact matches:

  * may canonicalize output labels
  * may lock fields against repair
  * are config-gated and auditable

Disease grounding specifics:

* Human Disease Ontology (DOID) is primary
* NCIT is queried only as a gated fallback
* Fallback triggering is lexical, deterministic, and configurable

---

## Validation and Repair Model (Frozen)

* Validation categories and decision routing are unchanged.
* Repairs remain:

  * field-scoped
  * attempt-bounded
  * globally bounded
* Locked fields are protected from backend repair overwrites.

---

## RAG and Retrieval (Frozen)

* RAG is:

  * read-only
  * deterministic
  * fallback-only
  * non-decisional
* Retrieval configuration lives under:

```
rag.*
rag.ontology.*
```

---

## Curator UI State (v0.7)

The curator UI has been significantly refined while preserving backend semantics.

Key properties:

* Table is the primary navigation surface
* GSM details are shown in modal popups
* Field status dashboard summarizes backend confidence signals
* Structured evidence panels expose grounding facts
* Overrides are:

  * explicit
  * session-only
  * non-persistent
  * auditable

UI guarantees:

* UI never alters backend logic
* UI never triggers inference, repair, or grounding
* UI never changes schema

---

## What Is Locked

The following must not be revisited without explicit architectural approval:

* Core pipeline ordering
* 8-field output schema
* Deterministic decision routing
* Ontology grounding semantics
* Repair loop structure
* RAG behavior

---

## What Is Open for the Next Milestone

The next milestone may:

* Re-walk the entire pipeline end-to-end
* Identify and fix edge cases
* Improve robustness, diagnostics, and tests
* Make small, ticketed backend fixes

As long as architectural invariants remain intact.

---

## How to Resume Work

To start a new session:

1. Read `docs/whitepaper.md`
2. Read `docs/milestones/v0.7-curator-ui.md`
3. Use this checkpoint as the current truth
4. Propose new work via tickets only

---

**Checkpoint status:** ARCHIVED
