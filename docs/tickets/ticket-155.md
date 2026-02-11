# Ticket #155: Redesign UI export to match `geo-gsm-summarize` (two CSV outputs)

## Background

The project now has a clear workflow separation:

- `geo-gsm-annotate` produces backend artifacts (authoritative, no overrides applied)
- Curator UI performs explicit overrides
- `geo-gsm-summarize` is the authoritative post-curation exporter that applies saved overrides and emits:
  - GSM-level CSV (8 canonical fields)
  - GSE-level CSV (7 fields)

The UI export panel should align with this workflow and produce the same two CSV outputs.

## Problem Statement

The current UI export experience is oriented around a single export action and does not clearly reflect the new canonical export model (two CSVs, summarize-style). This makes it harder for curators to know which export artifact corresponds to the recommended workflow.

## Proposed Change

Redesign the UI export section to export the two CSV artifacts consistent with `geo-gsm-summarize`:

1. Replace the single “Export ALL final annotations as CSV” action with two explicit actions:
   - “Export GSM CSV (8 fields)”
   - “Export GSE CSV (7 fields)”

2. Export semantics must match `geo-gsm-summarize`:
   - Apply **saved** curator overrides (persistent overrides on disk)
   - Do **not** re-run backend validation, repair, or ontology grounding
   - Do **not** apply unsaved session-only edits unless they have been saved as overrides

3. Output definitions
   - GSM CSV: exactly the 8 canonical fields
   - GSE CSV: GSE-level summary CSV as produced by `geo-gsm-summarize` (7 fields)

4. Implementation constraint (pick one, but preserve semantics)
   - Preferred: reuse the same internal summarization function/module used by `geo-gsm-summarize`
   - Acceptable: invoke `geo-gsm-summarize` from the UI as a subprocess, capturing the two CSV outputs for download
   - Either way, the exported bytes must be identical (or intentionally equivalent) to the CLI outputs for the same input directory and saved overrides.

5. UI clarity
   - Add brief one-line helper text under the export buttons:
     “Exports are equivalent to geo-gsm-summarize and apply saved overrides only.”

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change (policy-spec.md must be updated)

## Acceptance Criteria

- UI provides two export buttons: GSM CSV and GSE CSV.
- When no overrides are saved, exports still work (backend-derived values only).
- When overrides are saved, exports reflect those overrides.
- Unsaved session edits are not included unless saved.
- Exported CSV formats match the CLI `geo-gsm-summarize` outputs for the same directory (field set and row structure).
- No new backend processing occurs during export.

## Non-Goals

- No changes to CLI behavior.
- No changes to backend output artifacts.
- No new export formats beyond the two CSVs.
- No auto-save of overrides as part of export.

## Constraints

- UI must not reinterpret backend evidence or flags.
- Export must be deterministic and auditable, consistent with existing override application rules.
- If `geo-gsm-summarize` execution fails (if invoked), UI must show a clear error message without changing state.

## Guiding Principle

**One workflow, one meaning.**  
UI export should match the canonical summarize workflow and avoid ambiguity.

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-155.md` and paste this ticket verbatim.
