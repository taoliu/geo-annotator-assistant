# Ticket #105: Override Diff and Confidence View in GSM Detail Modal

## Background

Curator overrides are first-class, explicit input artifacts in the system.
They are intentionally powerful, but also intentionally non-authoritative:
overrides do not retrigger inference, repair, or ontology grounding.

In the current Curator UI (v0.7), overrides are functional but require curators
to mentally reconstruct:
- what the backend originally produced,
- what signals (flags, locks, terminal states) remain in effect,
- what exactly changed as a result of the override.

This increases hesitation and review time, especially for high-confidence
backend outputs.

## Problem Statement

The UI does not currently provide a **clear before/after comparison** when a
curator applies an override.

Specifically:
- Curators cannot easily see which backend signals are resolved vs unchanged.
- It is unclear which fields are overridden versus still governed by backend.
- The safety model (“override does not retrigger backend”) is not visually
  reinforced at the moment of action.

This is a UI confidence and transparency issue, not a backend gap.

## Proposed Change (UI Only)

Introduce a **read-only override diff and confidence view** within the GSM
detail modal.

### Inputs (Read-Only)

- `curation.jsonl`
  - backend field values
  - `final_decision`
  - `primary_failure`
  - `flags`
- `evidence.jsonl`
  - grounding, repair, and fallback diagnostics
- session override state (in-memory only)

### UI Behavior

1. **Before / After Field Diff**

When one or more overrides are present:
- Display a compact diff view per overridden field:
  - backend value → overridden value
- Non-overridden fields are shown as unchanged.

2. **Signal Persistence Summary**

Visually indicate:
- which backend flags remain active,
- which flags are resolved only by human judgment,
- that backend locks and terminal states are not recomputed.

This is descriptive only; no logic is added.

3. **Override Confidence Reminder**

Include a short, static reminder near the override controls:
- “Overrides do not retrigger validation, repair, or ontology grounding.”
- “All backend flags remain visible for audit.”

4. **Badge Integration**

- OVERRIDDEN badge remains on fields.
- Backend badges (LOCKED, TERMINAL, REPAIRED) remain visible and are not hidden
  by overrides.

### Visual Placement

- Diff view appears inline in the GSM detail modal when overrides exist.
- Collapsible by default to avoid clutter.

## Why No Backend Change Is Required

- Backend values are already present in `curation.jsonl`.
- Overrides already exist as in-memory UI state.
- The diff is a pure UI comparison with no side effects.

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change

## Acceptance Criteria

1. Curators can clearly see backend values vs overridden values.
2. Backend flags and badges remain visible and unchanged.
3. No backend logic is retriggered or simulated.
4. No JSONL files are modified.
5. UI reinforces override safety and auditability.

## Non-Goals

- No override validation or enforcement.
- No override recommendations.
- No persistence or learning from overrides.
- No changes to backend decision semantics.

## Constraints

- Backend outputs remain authoritative.
- UI must not reinterpret backend intent.
- Determinism and auditability must be preserved.

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-105.md` and paste this ticket verbatim.
