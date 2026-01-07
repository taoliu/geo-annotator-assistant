Below are **clean, ready-to-commit updates** for **README.md** and **docs/RESUME.md**, aligned with the v0.3 whitepaper and milestones you just finalized.

I kept them:

* concise,
* factual,
* architecture-consistent,
* curator-facing (README),
* contributor- and AI-session-facing (RESUME).

No speculative v0.4 claims are included.

---

## README.md (v0.3)

````markdown
# GEO GSM Annotator Agent

A deterministic, ontology-aware annotation pipeline for GEO GSM metadata, combining large language models with rule-based validation and bounded repair loops.

---

## Overview

The GEO GSM Annotator Agent extracts and standardizes sample-level (GSM) metadata from GEO using:

- LLM-based candidate generation
- Deterministic validators
- Ontology grounding (EFO, Uberon, Cellosaurus, DO)
- Field-scoped repair and fallback policies
- Fully auditable decision logs

The system is designed for **semi-automated curation**, not blind automation.

---

## Output Schema (Stable)

Each GSM record produces exactly eight fields:

- `gse_accession`
- `gsm_accession`
- `data_type`
- `organism`
- `tissue_type`
- `cell_line`
- `disease`
- `treatment`

This schema is invariant across v0.x.

---

## Key Features (v0.3)

- Fully wired deterministic repair loop
- Ontology grounding via ChromaDB
- Synonym-aware matching for disease and data_type
- Field-scoped repair and fallback logic
- Terminal fallback values (`Unknown`, `No`) with anti-cycling guarantees
- GSE-level batch execution with per-GSM independence
- Curator-ready outputs:
  - annotations
  - flagged samples
  - structured audit logs

---

## What This Tool Does *Not* Do

- No automatic learning from curator feedback
- No UI or interactive curation interface (planned for v0.4)
- No blind propagation of labels across GSMs
- No ontology mutation or online training

---

## Usage

### Run on a single GSM

```bash
uv run python -m agent.cli \
  --gsm GSM123456 \
  --config config/example_config.yaml
````

### Run on a GSE accession

```bash
uv run python -m agent.cli \
  --gse GSE123456 \
  --output-dir outputs/GSE123456 \
  --config config/example_config.yaml
```

### Run on pre-built JSONL contexts

```bash
uv run python -m agent.cli \
  --jsonl contexts.jsonl \
  --config config/example_config.yaml
```

---

## Outputs

Unless `--dry-run` is used, the pipeline writes:

* `annotations.jsonl`
* `audit.jsonl`
* `flagged.jsonl`

All decisions are reproducible and explainable from audit logs.

---

## Development Model

* Architecture decisions live in `docs/whitepaper.md`
* Milestones live in `docs/milestones/`
* All changes are tracked via tickets in `docs/tickets/`
* Tests must pass under `uv run pytest`

---

## License and Status

Research and curation support tool.
Not intended for clinical or diagnostic use.

````

---

