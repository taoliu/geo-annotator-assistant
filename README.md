# GEO GSM Annotator Agent

A deterministic, audit-first system for annotating and standardizing **GEO sample-level (GSM)** metadata with explicit human oversight.

---

## What this project does

GEO GSM Annotator Agent processes GEO samples (GSMs) and produces a **fixed, standardized metadata record** for each sample.

Key properties:

* Uses LLMs for **proposal generation only**
* Makes **deterministic decisions** via validation and routing logic
* Applies **ontology grounding for validation and normalization**, not inference
* Supports **bounded repair loops** for common failures
* Emits **structured audit artifacts** for every decision
* Allows **explicit, session-only human overrides**

The system is designed for **correctness, transparency, and curator trust**.

---

## Output contract (invariant)

Each GSM produces **exactly 8 output fields**:

* `gse_accession`
* `gsm_accession`
* `data_type`
* `organism`
* `tissue_type`
* `cell_line`
* `disease`
* `treatment`

No additional fields may appear in final outputs. Ontology IDs and diagnostics are recorded only in audit artifacts.

---

## Output artifacts

The pipeline emits multiple artifacts, but only one is **canonical** and schema-governed. UI-facing and diagnostic files are derived and **must not** be treated as final output.

* **`annotations.jsonl`**
  * Canonical final output
  * Exactly 8 fields per GSM:
    * `gse_accession`
    * `gsm_accession`
    * `data_type`
    * `organism`
    * `tissue_type`
    * `cell_line`
    * `disease`
    * `treatment`
  * Governed by the whitepaper's output contract

* **`audit.jsonl`**
  * Authoritative diagnostics and execution trace
  * Validation, ontology grounding, repair history, decision routing
  * Not schema-restricted

* **`curation.jsonl` / `curation.tsv`**
  * UI-facing, non-canonical, derived artifacts
  * May include decisions, flags, ontology status summaries
  * Must not be treated as schema-governed final output

* **`flagged.jsonl`**
  * Subset view of GSMs requiring curator attention
  * Derived, non-authoritative

* **`evidence.jsonl`**
  * Structured evidence snapshots for UI and review
  * Read-only, diagnostic

* **`gse_consistency.json`**
  * Advisory cross-GSM diagnostics
  * Must not influence GSM-level decisions

* **`gse_field_values.jsonl`**
  * Per-GSE field value summaries for diagnostics
  * Derived, non-authoritative

LLM caching exists, is deterministic, and is **disabled by default** (enable via config).

---

## High-level pipeline

1. Context ingestion
2. Prompt construction
3. LLM proposal generation
4. Deterministic validation
5. Ontology grounding (validation only)
6. Decision routing
7. Bounded repair (if needed)
8. Final decision
9. Audit emission

The pipeline order is fixed and must not be altered.

---

## Architecture and governance

This repository follows a strict separation of concerns:

* **Whitepaper** (`docs/whitepaper.md`): architectural law and invariants
* **Milestones** (`docs/milestones/`): medium-term system state
* **Checkpoints** (`docs/checkpoints/`): session reset anchors
* **Tickets** (`docs/tickets/`): short-term, permitted work

If a change conflicts with the whitepaper, it is not allowed.

---

## Curator UI (v0.7)

The curator UI is designed to expose backend decisions clearly without reinterpreting them.

Key features:

* Table-first interface for large GSEs
* GSM detail inspection via modal popups
* Field status dashboard (locked, canonicalized, ambiguous, overridden)
* Structured evidence panels for ontology grounding
* Safe, session-only override workflows
* Table-level triage and filters

The UI is non-authoritative and never alters backend logic.

---

## Command-line usage

### Backend annotation

```bash
geo-gsm-annotate run-gse --gse GSEXXXXX
```

Other backend subcommands exist for single GSM runs and diagnostics. See `geo-gsm-annotate --help`.

### Term standardization utility

```bash
geo-gsm-annotate standardize-terms -i curated.jsonl
```

This command applies **ontology grounding and canonicalization only**, without LLMs, repair loops, or learning.

---

## Overrides and exports

* Overrides are explicit, session-only inputs
* Overrides do not retrigger inference, validation, or grounding
* Exported overrides are deterministic and auditable

Overrides are treated as curator judgments, not learned state.

---

## What this project does not do

* No schema expansion
* No learning from human edits
* No persistence of UI state
* No ontology mutation
* No autonomous annotation

---

## Development workflow

* All work must be ticketed under `docs/tickets/`
* Backend semantics are frozen post-v0.6
* UI changes must not introduce backend logic
* Tests are required for all changes

Run tests with:

```bash
uv run pytest -q
```

---

## Getting started

1. Read `docs/whitepaper.md`
2. Read the latest milestone document
3. Check the most recent checkpoint
4. Start new work via a ticket

---

## License

See `LICENSE`.

---

## Summary

GEO GSM Annotator Agent is a **human-governed, deterministic annotation system** designed to make large-scale GSM metadata curation reliable, auditable, and scalable.
