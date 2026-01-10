# GEO GSM Annotator Agent — Project Resume

## Project Overview

The GEO GSM Annotator Agent is a semi-automated system for extracting, validating,
and standardizing **sample-level (GSM)** metadata from the Gene Expression Omnibus (GEO).

The system combines:

* large language models (LLMs) for proposal generation,
* deterministic validators and decision logic,
* ontology grounding for normalization and confidence assessment,
* bounded, field-scoped repair loops,
* and explicit, auditable human overrides.

The project is designed for **determinism, auditability, and controlled extensibility**.

---

## Current Status

**Backend:** Stable and frozen (post-v0.6)
**UI:** Local curator UI implemented (v0.5), further improvements planned
**Persistence / Learning:** Not implemented by design

The backend is considered **production-stable** for further UI-focused development.

---

## Latest Completed Milestone

### v0.6 — RAG & Validation Robustness (CLOSED)

Milestone v0.6 strengthened correctness, determinism, and performance of the backend
without changing architectural invariants.

Key outcomes:

* Deterministic-first ontology retrieval (exact match before vector fallback)
* Formalized terminal exact match semantics
* Canonicalization to ontology labels for exact matches (config-gated)
* Field locking to prevent repair overwrites on exact matches (config-gated)
* Controlled disease ontology fallback (DOID → NCIT) with lexical gating
* Elimination of unnecessary embedding calls
* Explicit embedding device control (`cpu`, `cuda`, `mps`)

No changes were made to the 8-field output schema or pipeline ordering.

---

## Backend Guarantees

The backend guarantees the following properties:

* Exactly 8 output fields per GSM
* Deterministic decision routing
* Bounded repair loops
* Read-only, non-decisional RAG
* Fully auditable execution

Ontology grounding:

* Is validation and normalization only
* Never performs inference
* May deterministically canonicalize labels on terminal exact matches

---

## Curator UI (v0.5)

A local curator UI is available with the following properties:

* Read-only by default
* Evidence-driven field highlighting
* Session-only editing
* Deterministic export of backend-compatible `overrides.jsonl`

The UI introduces no persistence, learning, or inference.

---

## Documentation Map

* `docs/whitepaper.md` — long-term architectural invariants (authoritative)
* `docs/milestones/` — milestone-level system evolution
* `docs/checkpoints/` — session reset and handoff anchors
* `docs/tickets/` — short-term implementation tasks

---

## Next Planned Milestone

### v0.7 — Curator UI Refinement

Planned focus:

* UI usability improvements
* Better visualization of ontology grounding and evidence
* Safer and clearer override workflows

Backend semantics introduced in v0.6 are considered **locked** unless explicitly revised.

---

## Development Model

* Architectural decisions are defined in the whitepaper
* Work is executed strictly via tickets
* ChatGPT acts as architect and reviewer
* Codex CLI handles implementation

This resume reflects the authoritative project state as of **post-v0.6**.
