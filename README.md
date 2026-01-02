# geo-gsm-annotator-agent

Ontology-grounded AI agent to annotate GEO **GSM** sample metadata.

## What this repo contains
- Agent orchestration (single GSM and batch)
- Prompt template management
- Ontology grounding via local ChromaDB (read-only retrieval)
- Deterministic validation + decision engine
- JSONL outputs: annotations, audit, flagged-for-review

## High-level flow
1) Fetch+parse GSM (external dependency) -> JSONL context  
2) Fine-tuned LLM proposes labels  
3) Validate (format + semantics + ontology grounding + consistency)  
4) Targeted repair if needed (bounded)  
5) Write outputs + audit logs; flag ambiguous cases

## Repo status
This is a skeleton with module boundaries and stable file paths. Implementations are intentionally minimal.

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
