# GEO GSM Annotator Agent

A deterministic, auditable system for extracting and standardizing **sample-level (GSM)** metadata from the NCBI Gene Expression Omnibus (GEO).

---

## Overview

The GEO GSM Annotator Agent combines large language models (LLMs) with strict
deterministic validation, ontology grounding, and bounded repair loops to
produce **reliable, reviewable GSM annotations**.

The system is designed to:

* scale to large GSEs,
* avoid silent inference,
* preserve auditability,
* and support explicit human oversight.

---

## Key Properties

* **Deterministic pipeline** — LLMs propose; deterministic logic decides
* **Fixed output schema** — exactly 8 fields per GSM
* **Evidence-first validation** — unsupported inference is rejected or repaired
* **Ontology grounding** — normalization and confidence assessment only
* **Deterministic-first retrieval** — exact matches before vector fallback
* **Auditable execution** — full structured audit artifacts
* **No learning or persistence** — by design

---

## Output Schema (Invariant)

Each GSM record produces exactly the following fields:

```
gse_accession
gsm_accession
data_type
organism
tissue_type
cell_line
disease
treatment
```

This schema is immutable within v0.x.

---

## Ontology Grounding (v0.6+)

Ontology grounding is used for **validation and normalization**, not inference.

Current behavior:

* Deterministic exact matches are preferred
* Vector similarity search is fallback-only
* Terminal exact matches may:

  * canonicalize output labels
  * lock fields against later repair (config-gated)
* Disease grounding uses a controlled fallback:

  * Human Disease Ontology (DOID) primary
  * NCIT secondary, gated by malignant-neoplasm lexical triggers

---

## Curator UI

A local curator UI is available with the following characteristics:

* Read-only by default
* Evidence-driven field highlighting
* Session-only editing
* Deterministic export of `overrides.jsonl`

The UI introduces no persistence or learning.

---

## Repository Structure (Simplified)

```
config/          # configuration examples
src/             # backend implementation
docs/            # whitepaper, milestones, checkpoints, tickets
```

---

## Documentation

* **Architecture:** `docs/whitepaper.md`
* **Milestones:** `docs/milestones/`
* **Checkpoints:** `docs/checkpoints/`
* **Tickets:** `docs/tickets/`

New contributors should start with the whitepaper.

---

## Development Model

* Architectural rules are defined in the whitepaper
* All changes are ticket-driven
* ChatGPT acts as architect and reviewer
* Codex CLI handles implementation

---

## Status

* Backend: stable and frozen (post-v0.6)
* Current focus: curator UI refinement (v0.7)

---

## License

MIT license.

---

