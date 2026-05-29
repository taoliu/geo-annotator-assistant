# Curator UI (v0.7, Read-Only)

## Run locally

From the repository root:

```
gaa-ui --input-dir <DIR>
```

Where `<DIR>` contains:

- `curation.jsonl`
- `evidence.jsonl`
- `suggestions.jsonl` (optional)
- `audit.jsonl` (optional; provides initial LLM proposals)

### Multi-GSE roots

If `<DIR>` contains immediate subdirectories named `GSE*`, the UI scans them and
loads each valid GSE. A GSE switcher appears in the sidebar, and skipped
directories are listed with reasons. This mode is read-only and does not
aggregate across GSEs.

The UI is read-only and does not write any files unless you explicitly export overrides.

## Primary navigation

- The GSM table is the primary navigation surface.
- Select a table row to open GSM details in a modal (table -> modal).
- Closing the modal returns you to the table without changing backend data.

## GSM detail modal

The modal presents GSM detail sections and review signals. At the top is the
Field Status Dashboard.

### Summary-first layout

The modal now opens with a compact decision summary, followed by the field
status dashboard. Deep evidence is collapsed by default and can be expanded on
demand. All information remains available, but high-signal elements are surfaced
first for faster scanning.

### Field Status Dashboard

- Shows all 8 output fields:
  `data_type`, `organism`, `tissue_type`, `cell_line`, `disease`, `treatment`,
  `gse_accession`, `gsm_accession`.
- Displays the backend value, optional LLM original (from `audit.jsonl`), and
  any session override.
- Displays one or more status badges derived from backend audit signals and
  session overrides.

### Status badges

Badges are informational only; they do not block edits or alter backend logic.

- LOCKED: field locked by backend due to a terminal exact match.
- TERMINAL: backend applied a terminal fallback value.
- REPAIRED: backend repair loop attempted or updated this field.
- CANONICALIZED: backend replaced the value with an ontology canonical label.
- TERMINAL EXACT: ontology grounding returned a terminal exact match.
- AMBIGUOUS / NO MATCH: grounding was ambiguous or failed (if available).
- OVERRIDDEN: current value differs from backend due to a session override.

Ontology grounding signals are visible but non-authoritative.

### Evidence panels

Evidence panels show structured, read-only diagnostics from `evidence.jsonl`
and optional advisory signals from `suggestions.jsonl`, such as:

- grounding status, match type, and scores
- repair attempts and fallbacks
- field-level review flags

Intentionally not shown:

- free-text rationale or commentary
- hidden model reasoning traces
- new analysis created by the UI

### Optional audit signals

If `audit.jsonl` is present, the modal displays the initial LLM proposal
per field (from `llm_parsed_outputs[0]`). These values are read-only and do
not affect backend outputs, validation, or decisions.

## Overrides and editing

- Overrides can be persisted per GSE in `overrides.jsonl`.
- If `overrides.jsonl` is present in the active GSE directory, it is loaded on startup.
- Overrides do not retrigger inference, repair, or ontology grounding.
- Overrides may replace values even when canonicalized or terminal exact.
- Exported overrides are explicit input artifacts, not learned or persisted
  state.
- The UI may show soft warnings or confirmations when overriding high-confidence
  signals, but it never hard-blocks edits.

### Exports

- **Save overrides** writes `<GSE_DIR>/overrides.jsonl`.
- **Export final annotations** creates `annotations.final.jsonl` with exactly the
  8 output fields and applies overrides without re-running backend logic.

## Ontology confidence vs correctness

Ontology canonicalization indicates deterministic normalization, not
correctness. Terminal exact indicates a perfect ontology match, not ground
truth. Human curator judgment remains final.

## Non-goals and guardrails

The Curator UI does not:

- persist changes or learn from edits
- trigger or modify backend logic
- change schemas or output formats
- propagate decisions across GSMs
