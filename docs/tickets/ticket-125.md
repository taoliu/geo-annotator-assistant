# Ticket #125: Hide redundant diagnostic columns and move all per-field diagnostics into evidence-based hover tooltips

## Background

With AG Grid tooltips in place, curators can inspect per-field diagnostics directly.
However, the table still displays multiple diagnostic columns that are now visually
distracting and redundant.

All per-field diagnostic information is already present in `evidence.jsonl`, which is
authoritative and sufficient for UI inspection.

## Problem Statement

The following diagnostic columns clutter the table and duplicate information that can
be shown contextually in per-cell tooltips:

- Review flags
- Terminal fallbacks
- Outliers
- Primary failure
- Flag summary
- flagged_fields

In addition, diagnostics such as fallback and low-confidence states are currently shown
out of context rather than attached to the specific field they affect.

## Proposed Change

### A) Hide redundant diagnostic columns
Remove (or hide by default) the following columns from the curation table:

- `review_flags`
- `terminal_fallbacks`
- `outliers`
- `primary_failure`
- `flag_summary`
- `flagged_fields`

These columns must not appear in the default curator view.

(They may remain in the internal row model if needed for UI logic, but must not be visible.)

### B) Use evidence.jsonl as the sole source of per-field diagnostics in tooltips
For each of the five essential biology columns:

- `data_type`
- `organism`
- `tissue_type`
- `cell_line`
- `disease`

extend the hover tooltip to display **read-only diagnostics from `evidence.jsonl`** for
the hovered GSM + field:

From `evidence_by_field[field]`, show:

- `Attempts: <int>`
- `Ontology status: <string or empty>`
- `Terminal fallback: <true|false>`
- `Evidence flags: <comma-separated list or “none”>`

If `Evidence flags` is non-empty, they represent the field’s issue state and must be
displayed clearly.

If `Ontology status == FALLBACK` and `Evidence flags` is empty, show it as informational
only (e.g., “Ontology status: FALLBACK”), and it must NOT be treated as a warning.

### C) Maintain existing tooltip content
Keep existing tooltip lines already implemented, including:

- Displayed value
- Backend-derived value
- LLM original value
- Ontology alternates (if already present in loaded artifacts)

Append evidence diagnostics in a stable, consistent order.

### D) Maintain existing highlighting semantics
Cell highlighting for essential columns remains:

- Highlight **if and only if**
  `len(evidence_by_field[field].flags) > 0`

Do not highlight based on:
- ontology_status alone
- terminal_fallback
- attempts
- any summary columns

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change (policy-spec.md must be updated)

## Acceptance Criteria

- The listed diagnostic columns are not visible in the default table view.
- For any essential field cell, hovering shows diagnostics sourced exclusively from
  `evidence.jsonl`.
- Fields with `FALLBACK` but no evidence flags are not highlighted.
- Fields with non-empty evidence flags are highlighted and show those flags in the tooltip.
- No backend execution is triggered.
- No backend artifacts are modified.

## Non-Goals

- Do not reintroduce `primary_failure` as a separate UI signal.
- Do not infer or synthesize new diagnostics.
- Do not change backend decision semantics.

## Constraints

- UI-only change.
- evidence.jsonl is treated as authoritative for per-field diagnostics.
- Tooltip content must remain concise and readable.

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-125.md` and paste this ticket verbatim.
