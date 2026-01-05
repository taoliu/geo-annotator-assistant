# geo-gsm-annotator-agent

Ontology-grounded AI agent to annotate GEO **GSM** sample metadata.

## What this repo contains
- Agent orchestration (single GSM and batch)
- Prompt template management
- Ontology grounding via local ChromaDB (read-only retrieval)
- Deterministic validation + decision engine
- JSONL outputs: annotations, audit, flagged-for-review

## Project Status

The project is under active development.

- Milestone v0.2 (Ontology grounding and evidence-first repair) is complete.
- Current focus is shifting toward labeling policy and semantic conventions.

See:
- `docs/whitepaper.md` for long-term design
- `docs/milestones/` for development phases
- `docs/tickets/` for execution-level tasks

## High-level flow
1) Fetch+parse GSM (external dependency) -> JSONL context  
2) Fine-tuned LLM proposes labels  
3) Validate (format + semantics + ontology grounding + consistency)  
4) Targeted repair if needed (bounded)  
5) Write outputs + audit logs; flag ambiguous cases

## Expected external dependencies
- A parser/downloader package or script that produces the JSONL context given a GSM accession.
- A fine-tuned LLM caller (API client or local runner).
- A local ChromaDB persist directory for ontologies.

## Quick start (after implementations are filled)
```bash
python -m agent.cli --gsm GSM123 --output-dir outputs --config config/example_config.yaml
```
If you run from the repo without installing, use:
```bash
PYTHONPATH=src python -m agent.cli --gsm GSM123 --output-dir outputs --config config/example_config.yaml
```
