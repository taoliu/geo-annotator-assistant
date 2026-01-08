# GEO GSM Annotator Agent

A deterministic, ontology-aware annotation pipeline for GEO **GSM-level metadata**, combining large language models with rule-based validation, bounded repair loops, and explicit human curation support.

---

## Overview

The GEO GSM Annotator Agent extracts, validates, repairs, and standardizes sample-level (GSM) metadata from the GEO database.

It is designed for **semi-automated curation**:

* LLMs propose candidate annotations
* Deterministic logic decides
* Humans can review and explicitly override results

The system emphasizes **auditability, reproducibility, and curator control**, rather than blind automation.

---

## Output Schema (Stable)

Each GSM record produces **exactly eight fields**:

* `gse_accession`
* `gsm_accession`
* `data_type`
* `organism`
* `tissue_type`
* `cell_line`
* `disease`
* `treatment`

This schema is invariant across v0.x.

---

## Key Features (v0.4)

### Deterministic annotation pipeline

* LLM-based candidate generation
* Format and semantic validation
* Ontology grounding (read-only)
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
  Lossless JSON mirror of `curation.tsv` for tooling and UI

* **`evidence.jsonl`**
  Structural diagnostic evidence derived from audits:

  * repair attempts
  * terminal fallback usage
  * ontology grounding status
  * field-level flags
    (no free-text explanations, no new inference)

* **`suggestions.jsonl`** (optional)
  Advisory cross-GSM diagnostics highlighting outliers or singletons
  Suggestions never modify outputs

* **`audit.jsonl`**
  Mandatory, structured audit log for all decisions

### Explicit human overrides

* Human corrections are provided via **`overrides.jsonl`**
* Overrides:

  * are explicit inputs
  * apply after automated processing
  * do not trigger re-inference
* All overrides are recorded with full audit provenance

---

## What This Tool Does *Not* Do

* No automatic learning from curator feedback
* No forced label propagation across GSMs
* No ontology mutation or online training
* No interactive UI (planned for a future release)

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

* `suggestions.jsonl` (when enabled)

All results are reproducible and explainable from audit artifacts.

---

## Development Model

* **Whitepaper**: long-term architecture (`docs/whitepaper.md`)
* **Milestones**: medium-term state (`docs/milestones/`)
* **Checkpoints**: operational memory (`docs/checkpoints/`)
* **Tickets**: executable work units (`docs/tickets/`)

All code changes must correspond to a ticket.

---

## License and Status

Research and curation support tool.
Not intended for clinical or diagnostic use.

---
