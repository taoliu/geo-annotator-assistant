# Ticket #101: Flag Severity and Category Visualization in Curator UI

## Background

With v0.9 policy consolidation, `curation.jsonl` now contains a richer and denser
set of flags and primary failures. In the current Curator UI (v0.7), all flags
are displayed with roughly equal visual weight, making it hard for curators to
quickly distinguish:

- policy-terminal conditions,
- ambiguity requiring judgment,
- informational or expected flags.

This increases review time and cognitive load without improving correctness.

## Problem Statement

The UI currently exposes flags as a flat list derived from `curation.jsonl` and
`evidence.jsonl`, but does not convey *why* a record is FLAGGED in a way that
matches curator decision-making needs.

Specifically:
- Curators cannot quickly tell whether a FLAGGED record is:
  - blocked by a hard policy outcome,
  - ambiguous and requiring judgment,
  - or merely carrying informational signals.
- Primary failure is not visually distinguished from secondary flags.
- As flag volume increases under v0.9, visual salience has not scaled.

This is a **presentation and ergonomics issue only**, not a backend deficiency.

## Proposed Change (UI Only)

Introduce **flag severity tiers and visual categorization** in the Curator UI,
derived entirely from existing backend artifacts.

### Inputs (Read-Only)

- `curation.jsonl`
  - `final_decision`
  - `primary_failure`
  - `flags`
- `evidence.jsonl`
  - field-level grounding status
  - repair and fallback diagnostics
- `suggestions.jsonl` (optional, advisory only)

### UI Behavior

1. **Flag Categorization (Visual Only)**

   Group flags into UI-only severity categories, for example:

   - **Policy / Terminal**
     - terminal fallbacks
     - non-anatomical placeholders
     - model-identifier disease rules
   - **Ambiguity / Review Required**
     - ontology_low_confidence_*
     - ontology_ambiguous_*
     - evidence-first violations
   - **Informational**
     - canonicalization notices
     - generalization flags
     - advisory signals

   These categories are:
   - derived deterministically from existing flag names,
   - implemented purely in UI code,
   - not written back to any JSONL.

2. **Primary Failure Emphasis**

   - Visually highlight `primary_failure` from `curation.jsonl`.
   - Secondary flags are de-emphasized or grouped below.

3. **Visual Hierarchy**

   - Use consistent iconography and color severity levels.
   - Avoid reordering backend-provided flag lists in data.
   - Do not hide any flags.

4. **No Semantic Interpretation**

   - UI must not infer correctness, confidence, or suggested action.
   - All labeling is descriptive (“Policy”, “Ambiguous”), not prescriptive.

## Why No Backend Change Is Required

- All information needed already exists in:
  - `curation.jsonl` (decision + flags),
  - `evidence.jsonl` (diagnostics),
  - `suggestions.jsonl` (optional advisory context).
- Severity tiers are **UI presentation only** and do not alter:
  - validation logic,
  - repair semantics,
  - decision routing,
  - or audit artifacts.
- No new fields, schemas, or policies are introduced.

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change

## Acceptance Criteria

1. The GSM table and modal visually distinguish:
   - primary failure vs secondary flags,
   - policy-terminal vs ambiguous vs informational flags.
2. No JSONL files are modified or augmented.
3. All flags remain visible and traceable to backend outputs.
4. UI behavior remains strictly read-only.
5. Existing tests for UI state and flag display continue to pass or are updated
   only to reflect visual grouping, not logic changes.

## Non-Goals

- No reclassification or suppression of backend flags.
- No automatic curator recommendations.
- No override blocking or enforcement.
- No changes to backend decision logic.

## Constraints

- Backend outputs remain the single source of truth.
- UI must not invent new analytical states.
- Determinism and auditability must be preserved.

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-101.md` and paste this ticket verbatim.
