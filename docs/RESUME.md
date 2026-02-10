# GEO GSM Annotator Agent — Project Snapshot

## Purpose

**GEO GSM Annotator Agent** is a deterministic, audit-first system for annotating and
standardizing GEO sample-level (GSM) metadata with explicit human-in-the-loop curation.

The system prioritizes correctness, transparency, and reproducibility over automation.

---

## Current Status

- Backend semantics **frozen and authoritative as of v0.9**
- Curator web UI **production-ready as of v1.1**
- CLI ergonomics, batch safety, and ingest robustness **completed in v1.2**
- Validation, repair, ontology grounding, and reporting behavior consolidated
- Real-world GEO edge cases handled deterministically

---

## Core Capabilities

- Deterministic annotation pipeline producing **exactly 8 GSM fields**:
  - `gse_accession`, `gsm_accession`, `data_type`, `organism`,
    `tissue_type`, `cell_line`, `disease`, `treatment`
- Policy-governed validation, bounded repair, and explicit flagging
- Ontology grounding as **validation only**, never decisive
- Full audit trail for every GSM
- Explicit, persistent curator overrides

---

## Intended Workflow

1. Prepare a YAML configuration
2. Run `geo-gsm-annotate` on GSE(s)
3. Review and curate results via the web UI
4. Export final CSVs using `geo-gsm-summarize`

---

## Architectural Invariants

Treated as law:

- Fixed 8-field output schema
- Deterministic decision routing
- No learning from curator edits
- RAG as fallback only
- Ontologies as validation only
- Full auditability and replayability
- Human curator as final authority

Defined in `docs/whitepaper.md`.

---

## Intended Users

- Bioinformatics curators
- Data integration teams
- AI-assisted curation pipelines requiring auditability

---

## Repository Entry Points

- Agent CLI: `geo-gsm-annotate`
- Post-curation export CLI: `geo-gsm-summarize`
- Curator UI: `geo-gsm-ui`
