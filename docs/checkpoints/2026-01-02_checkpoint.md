# Project Checkpoint — 2026-01-02
## GEO GSM Metadata Annotator Agent

This document captures the current implementation status and next steps for the
`geo-gsm-annotator-agent` project. It is intended as a **handoff checkpoint**
for future development sessions (human or AI).

---

## 1. Project Goal (Reminder)

Build an **AI agent** that:
- Takes a **GEO GSM accession** as input
- Fetches and parses GSM + parent GSE metadata
- Uses an LLM to propose standardized labels
- Grounds labels against biomedical ontologies
- Applies deterministic validation and repair
- Produces high-quality, auditable GSM metadata
- Flags ambiguous samples for human review

Target output fields:
- data_type
- organism
- tissue_type
- cell_line
- disease
- treatment

---

## 2. Current Status (As of 2026-01-02)

### ✅ Walking skeleton complete

The system is fully runnable end-to-end **with stubs**, including:

```bash
uv run python -m agent.cli \
  --gsm GSM000000 \
  --config config/example_config.yaml \
  --output-dir /tmp/out
2. **AGENT-WS-014** — Integrate real LLM caller
3. **AGENT-WS-015** — Implement ontology grounders (ChromaDB)
4. **AGENT-WS-016** — Human review ingestion + override re-run

---

## 7. How to Resume This Project

To resume in a future session:

1. Read this checkpoint
2. Read `docs/whitepaper.md`
3. Inspect `tickets/` for completed tickets
4. Start with AGENT-WS-013
