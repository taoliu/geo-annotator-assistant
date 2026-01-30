# Ticket #103: Policy-Aware Explanatory Tooltips for Flags and Field Badges

## Background

After Tickets #101 and #102, the Curator UI will display richer visual signals:
- flag severity categories,
- primary failure emphasis,
- field-level state badges (LOCKED, TERMINAL, REPAIRED, OVERRIDDEN).

However, without concise explanations, curators may still need to open evidence
panels to understand *what a badge or flag actually means* in policy terms.

v0.9 policy semantics are explicit and stable, making them suitable for
**read-only UI explanations**.

## Problem Statement

The UI currently assumes that curators will interpret badges and flags correctly
based on prior knowledge or deep inspection of evidence panels.

Specifically:
- Badges like TERMINAL or LOCKED do not explain *why* they exist.
- Flag labels (e.g. `ontology_low_confidence_disease`) are technical and opaque.
- Curators hesitate before overriding because intent is unclear.

This is an explanation and discoverability issue, not a data or policy gap.

## Proposed Change (UI Only)

Add **concise, policy-aware explanatory tooltips** to flags and field state badges.

### Inputs (Read-Only)

- `curation.jsonl`
  - `flags`
  - `primary_failure`
  - `terminal_fallback_fields`
- `evidence.jsonl`
  - ontology grounding status
  - repair and fallback diagnostics
- UI-local mapping tables (static text only)

### Tooltip Behavior

1. **Field State Badges (from Ticket #102)**

Each badge displays a hover tooltip explaining:

- **LOCKED**
  - “Backend marked this field as final due to a deterministic ontology match or policy rule. The system will not attempt further repair.”
- **TERMINAL**
  - “This value is a policy-defined fallback (e.g. Unknown, No, Healthy). It reflects insufficient or non-actionable evidence, not correctness.”
- **REPAIRED**
  - “This value was modified by the backend repair loop after validation or ontology checks.”
- **OVERRIDDEN**
  - “This value was manually overridden in the current session. Overrides do not retrigger backend logic.”

2. **Flags**

- Hovering over a flag shows:
  - a short, human-readable explanation,
  - whether it reflects policy finality or ambiguity,
  - a reminder that flags are informational.

Example:
- `ontology_low_confidence_disease` →
  “The disease term partially matches an ontology entry, but confidence is below the acceptance threshold. Human review is recommended.”

3. **Primary Failure**

- Primary failure tooltip explains:
  - why this failure was selected over others,
  - that selection is deterministic,
  - that secondary flags still apply.

### Implementation Notes

- Tooltip text is **static, UI-defined**, and versioned with the UI.
- No dynamic reasoning or inference is performed.
- Tooltips must not imply correctness or recommend actions.

## Why No Backend Change Is Required

- All tooltip triggers come from existing fields in `curation.jsonl` and
  `evidence.jsonl`.
- Explanatory text reflects *documented v0.9 policy*, not new logic.
- No data is written back or transformed.

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change

## Acceptance Criteria

1. All field state badges display explanatory tooltips on hover.
2. All flags displayed in the UI have a human-readable tooltip.
3. Tooltip language is descriptive, neutral, and non-prescriptive.
4. No JSONL files are modified.
5. No new backend calls or computations are introduced.

## Non-Goals

- No inline policy editing.
- No automatic override suggestions.
- No new analytical states.
- No backend behavior changes.

## Constraints

- Backend remains the single source of truth.
- UI explanations must not diverge from documented v0.9 policy.
- Determinism and auditability must be preserved.

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-103.md` and paste this ticket verbatim.
