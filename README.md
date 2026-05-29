# GEO Annotator Assistant

Deterministic, audit-first annotation pipeline for GEO GSM metadata, with human curation and post-processing export.

## Intended Workflow

1. Prepare a YAML configuration.
2. Run `geo-gsm-annotate` on GSE(s).
3. Curate results in the web UI.
4. Export reporting CSVs with `geo-gsm-summarize` or similar functions on web UI.

Curator overrides are post-processing inputs. They are not accepted by `geo-gsm-annotate`.

## Install / Run

```bash
uv sync
```

Run tests:

```bash
uv run pytest -q
```

## CLI: `geo-gsm-annotate`

Primary backend runner.

Supported input modes (mutually exclusive):
- `--gsm`
- `--gsm-file`
- `--jsonl`
- `--gse`
- `--gse-file`
- `--gse-soft`

Core flags:
- `--config <YAML>` (required)
- `--output-dir <DIR>`
- `--emit-suggestions`
- `--dry-run` (run pipeline, skip file writes)
- `--verbose` (runtime milestone logs to stderr)

Subcommand:
- `geo-gsm-annotate standardize-terms ...`

Examples:

```bash
# Single GSE
uv run geo-gsm-annotate \
  --gse GSE161517 \
  --config config/example_config.yaml \
  --output-dir out/run_single

# Multi-GSE batch from file
uv run geo-gsm-annotate \
  --gse-file gse_list.txt \
  --config config/example_config.yaml \
  --output-dir out/batch \
  --verbose

# Dry run
uv run geo-gsm-annotate \
  --gse GSE161517 \
  --config config/example_config.yaml \
  --dry-run
```

Batch behavior:
- `--gse-file` processes each GSE independently and writes per-GSE outputs.
- Local SOFT missing/skip cases are handled per GSE (warnings + continue where applicable).

## Web UI: `geo-gsm-ui`

Human-in-the-loop curation interface over existing outputs.

```bash
uv run geo-gsm-ui --input-dir out/batch
```

Notes:
- Curators apply explicit overrides.
- UI actions do not rerun backend inference/validation/repair/grounding.
- Saved UI artifacts are reused by summarization.

## CLI: `geo-gsm-summarize`

Read-only export command for curated outputs.

```bash
uv run geo-gsm-summarize --input-dir out/batch --output-dir out/reports
```

Behavior:
- Scans one or more output directories (`GSE*` layout supported).
- Loads curation artifacts and applies overrides.
- Applies overrides here (or in UI), not during annotation.

Options:
- `--input-dir <DIR>` (required)
- `--overrides <PATH>` (explicit overrides source)
- `--output-dir <DIR>` (default: input dir)
- `--gsm-csv <NAME>` (default: `gsm_annotations.csv`)
- `--gse-csv <NAME>` (default: `gse_summary.csv`)
- `--strict` (fail on missing/unreadable GSE dirs; default is warn+skip)

Outputs:

1. GSM CSV (`gsm_annotations.csv` by default), exactly 8 fields:
- `gse_accession`
- `gsm_accession`
- `data_type`
- `organism`
- `tissue_type`
- `cell_line`
- `disease`
- `treatment`

2. GSE CSV (`gse_summary.csv` by default), exactly 7 fields:
- `gse_accession`
- `data_type`
- `organism`
- `tissue_type`
- `cell_line`
- `disease`
- `treatment`

Please note that the similar functions can be found on the web UI interface.

## Main Output Files from Annotation Runs

Per run / per GSE directory:
- `annotations.jsonl`
- `audit.jsonl`
- `flagged.jsonl`
- `curation.jsonl`
- `curation.tsv`
- `evidence.jsonl`
- `gse_consistency.json`
- `gse_field_values.jsonl`
- `suggestions.jsonl` (when `--emit-suggestions` is enabled)

## Optional Local GEO SOFT Mirror

Configured in YAML:

```yaml
ingest:
  geo_soft_local_dir: "/abs/path/to/geo/soft/mirror"
  geo_soft_on_missing: "remote"      # remote | skip | error
  geo_soft_remote_transport: "https" # https | ftp
```

## Governance

- Architecture and invariants: `docs/whitepaper.md`
- Policy semantics: `docs/policies/policy-spec.md`
- Ticketed changes: `docs/tickets/`

