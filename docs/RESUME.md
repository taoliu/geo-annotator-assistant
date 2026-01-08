# GEO GSM Annotator Agent — Project Resume

This document summarizes the current state, guarantees, and operating assumptions of the project.  
It is intended to help **new contributors and new AI coding sessions** resume work safely.

---

## Project Status

- Current milestone: **v0.3**
- Stability level: **backend-stable**
- Intended users: computational biologists and human curators
- Intended use: GSM-level metadata normalization and review

---

## What Exists and Works (v0.3)

### Core Pipeline

- Deterministic end-to-end pipeline:
  - LLM generation
  - format validation
  - semantic validation
  - ontology grounding
  - decision routing
  - bounded repair loop
- Fully wired across CLI, GSM, and GSE modes
- Outputs include `annotations.jsonl`, `audit.jsonl`, `flagged.jsonl`, `curation.tsv`, and `curation.jsonl` (lossless mirror)

### Repair and Validation

- Field-scoped repairs
- Per-field attempt limits
- Global repair limit
- Terminal fallback values
- Anti-cycling repair constraint
- Evidence-first semantics

### Ontology Integration

- ChromaDB-backed grounding
- Read-only ontology usage
- Deterministic thresholds
- Clear separation from semantic validation

### GSE Support

- GSE accession ingestion
- SOFT or prebuilt JSONL support
- Independent GSM decisions
- GSE-level summary reporting
- No forced label propagation

### Curation Inputs (v0.4 groundwork)

- Human corrections are expressed as an explicit `overrides.jsonl` input artifact (one JSON object per line)
- Each record targets a GSM + output field with a new value; optional metadata may include reason/curator/timestamp
- Overrides are validated on load but not applied to outputs yet

---

## What Is Explicitly Deferred

These are **intentional**, not missing:

- Interactive curator UI
- Manual override workflows
- Cross-GSM consensus voting
- Active learning or feedback loops

These are planned for **v0.4**.

---

## Invariants (Do Not Break)

- Output schema: exactly 8 fields
- Deterministic decision engine
- Audit logs are mandatory
- Ontology grounding is read-only
- No silent repair loops
- No hidden state between runs

If a change violates any of the above, it requires:
- a design discussion,
- a milestone update,
- and explicit documentation.

---

## How Work Is Organized

- **Whitepaper**: long-term architecture (`docs/whitepaper.md`)
- **Milestones**: state snapshots (`docs/milestones/`)
- **Checkpoints**: operational memory (`docs/checkpoints/`)
- **Tickets**: executable tasks (`docs/tickets/`)

All code changes must correspond to a ticket.

---

## Guidance for New AI / Codex Sessions

Before coding:

1. Read:
   - `docs/whitepaper.md`
   - latest milestone doc
   - latest checkpoint doc
2. Identify the active ticket number.
3. Do not redesign architecture unless explicitly instructed.
4. Prefer incremental, testable changes.

---

## Current Next Direction

- Close v0.3 with documentation alignment
- Begin v0.4 planning:
  - curator UI
  - human-in-the-loop workflows
  - review and override interfaces
