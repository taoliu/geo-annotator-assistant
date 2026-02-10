# Ticket #146: Stronger in-table visual distinction for overridden and flagged cells

## Background

Curators need to quickly see:
- which cells are flagged by backend evidence (needs attention)
- which cells have curator overrides applied

The current UI supports both concepts, but the distinction is visually subtle in a dense table.

## Problem Statement

In the curation table:

- Flagged cells/rows are not visually distinct enough from normal cells during scanning.
- Overridden cells are not visually distinct enough from model-proposed values.
- Selected-row styling can conflict with flagged/override cues, increasing confusion.

This increases review time and can lead to missed issues.

## Proposed Change

In the curation table UI (presentation only):

1. Overridden cell styling
   - Use a **green background** for cells that have a curator override applied.
   - This must reflect the override artifact state only (no inference).

2. Flagged cell styling
   - Use an **orange background** for cells that are flagged by backend evidence.
   - Flag detection must follow the existing invariant:
     - highlighting is permitted if and only if `evidence_by_field[field].flags` is non-empty.

3. Selected-row styling
   - Ensure selected-row styling is visually distinct from both green (override) and orange (flag) backgrounds.
   - If needed, use border/outline for selection rather than background fill, or choose a selection color that cannot be confused with green/orange.

4. Precedence rules (UI-only, deterministic)
   - If a cell is both overridden and flagged, apply a deterministic precedence rule and make it visually clear (for example: keep green background but add an orange border, or vice versa).
   - This rule must be documented in the UI help text/tooltips.

No changes to:
- backend flags
- failure routing
- evidence generation
- override persistence semantics

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change (policy-spec.md must be updated)

## Acceptance Criteria

- Overridden cells are rendered with a green background.
- Flagged cells are rendered with an orange background.
- Selected-row styling is clearly distinguishable from both green and orange and does not obscure them.
- If a cell is both overridden and flagged, the UI applies a deterministic combined style that remains readable and unambiguous.
- No additional diagnostics are synthesized; all flagging uses `evidence.jsonl` only.
- Unit/UI tests are updated or added to ensure:
  - override detection drives green styling
  - evidence flags drive orange styling
  - selection styling remains distinct

## Non-Goals

- No changes to decision logic, policy, or backend outputs.
- No introduction of summary diagnostic columns beyond what already exists.
- No new “inferred” warning signals.

## Constraints

- Do not reinterpret backend evidence.
- Do not compute new flags or “severity” scores.
- Preserve current table behavior and editing semantics; only styling/clarity changes are allowed.

## Guiding Principle

**Make state visible, not smarter.**  
Stronger visual distinctions improve curator efficiency while preserving backend authority.

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-146.md` and paste this ticket verbatim.
