# GEO GSM Annotator Agent

A deterministic, ontology-aware annotation system for GEO **GSM-level metadata**,
combining large language models with rule-based validation, bounded repair,
and explicit human curation.

The system is designed for **auditable, reproducible, curator-controlled**
metadata normalization rather than fully automated labeling.

---

## Overview

The GEO GSM Annotator Agent extracts, validates, repairs, and standardizes
sample-level (GSM) metadata from the GEO database.

It follows a **semi-automated curation model**:

* LLMs propose candidate annotations
* Deterministic logic validates and decides
* Humans review results and apply explicit overrides when needed

All decisions are recorded and explainable.

---

## Output Schema (Stable)

Each GSM record produces **exactly eight canonical fields**:

* `gse_accession`
* `gsm_accession`
* `data_type`
* `organism`
* `tissue_type`
* `cell_line`
* `disease`
* `treatment`

This schema is invariant across all v0.x releases.

---

## Key Features (v0.5)

### Deterministic annotation pipeline

* LLM-based proposal generation
* Format and semantic validation
* Read-only ontology grounding
* Field-scoped repair with bounded attempts
* Terminal fallback values with anti-cycling guarantees
* Fully ordered, deterministic execution

### Performance-stable at scale

* Local HuggingFace model is loaded **once per run**
* All GSMs reuse the same model instance
* Practical GSE-scale processing on a single GPU

### Curator-ready review artifacts

Each run may produce:

* **`curation.tsv`**  
  Human-readable tabular summary

* **`curation.jsonl`**  
  Lossless JSON mirror of `curation.tsv`

* **`evidence.jsonl`**  
  Structural diagnostic evidence derived strictly from audits:
  * repair attempts
  * terminal fallback usage
  * ontology grounding status
  * field-level flags  
  (no free-text rationale, no new inference)

* **`suggestions.jsonl`** (optional)  
  Advisory cross-GSM diagnostics highlighting outliers or singletons  
  Suggestions never modify outputs

* **`audit.jsonl`**  
  Mandatory, structured audit log for all decisions

---

## Human Curation Support

### Overrides (backend contract)

* Human corrections are provided via **`overrides.jsonl`**
* Each override targets:
  * one GSM
  * one canonical field
  * a new value
* Overrides:
  * apply after automated processing
  * do not trigger re-inference or re-grounding
* All applied overrides are fully audited

### Curator UI (v0.5)

* Local, Streamlit-based curator UI
* Read-only by default
* Loads:
  * `curation.jsonl`
  * `evidence.jsonl`
  * `suggestions.jsonl` (optional)
* Wide, searchable GSM table
* Per-GSM detail panels showing raw artifacts
* Evidence-derived field-level issue highlighting
* Explicit edit mode with inline table editing
* Deterministic export of backend-compatible `overrides.jsonl`

The UI introduces **no persistence, no learning, and no inference**.

---

## What This Tool Does *Not* Do

* No automatic learning from curator feedback
* No forced cross-GSM consensus or label propagation
* No ontology mutation or online training
* No hidden or persistent state

These exclusions are intentional design decisions.

---

## Usage

### Run on a single GSM

```bash
uv run python -m agent.cli \
  --gsm GSM123456 \
  --config config/example_config.yaml
```

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

### Apply curator overrides

```bash
uv run python -m agent.cli \
  --gse GSE123456 \
  --overrides overrides.jsonl \
  --config config/example_config.yaml
```

---

## Outputs

Unless `--dry-run` is used, the pipeline writes:

* `curation.tsv`
* `curation.jsonl`
* `evidence.jsonl`
* `audit.jsonl`

Optional outputs:

* `suggestions.jsonl`

All results are deterministic and reproducible.

---

## Development Model

* **Whitepaper** (`docs/whitepaper.md`)
  Long-term architectural invariants

* **Milestones** (`docs/milestones/`)
  Medium-term state snapshots

* **Checkpoints** (`docs/checkpoints/`)
  Operational handoff points

* **Tickets** (`docs/tickets/`)
  Executable work units

All code changes must correspond to a ticket.

---

## License and Status

Research and curation support tool.
Not intended for clinical or diagnostic use.
