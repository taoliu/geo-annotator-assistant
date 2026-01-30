# Ticket #102: Explicit Locked / Terminal / Repaired Field State Badges

## Background

In v0.9, backend behavior around **locked fields**, **terminal fallbacks**, and
**repair attempts** is now fully explicit and policy-driven. These states are
already encoded in `curation.jsonl` and `evidence.jsonl`.

However, in the current Curator UI (v0.7), curators must infer a field’s
mutability and history by scanning multiple badges and evidence panels. This
creates uncertainty about:

- whether a field can still be meaningfully overridden,
- whether the backend considers a value final,
- whether a value reflects a repair, a fallback, or a direct extraction.

This is a visibility and ergonomics issue, not a backend limitation.

## Problem Statement

The UI does not currently provide a **clear, at-a-glance answer** to the curator
question:

> “What is the backend’s stance on this field right now?”

Specifically:
- Locked fields are not visually distinguished from terminal fallbacks.
- Repaired fields do not clearly indicate that they were modified by the backend.
- Curators must open evidence panels to reconstruct field history.
- The cognitive cost of safe overrides is higher than necessary.

## Proposed Change (UI Only)

Introduce **explicit field-level state badges** that summarize backend intent,
derived entirely from existing audit signals.

### Inputs (Read-Only)

- `curation.jsonl`
  - `terminal_fallback_fields`
  - `attempts_by_field`
  - final field values
- `evidence.jsonl`
  - ontology match status
  - repair attempts and outcomes
  - canonicalization signals
- session override state (in-memory only)

### New UI Badges (Descriptive Only)

For each of the 8 output fields shown in the Field Status Dashboard:

1. **LOCKED**
   - Field is locked by backend due to terminal exact ontology match or policy.
   - Derived from existing lock / canonicalization signals.
   - Indicates backend will not repair this field further.

2. **TERMINAL**
   - Field value is a terminal fallback (e.g. `Unknown`, `No`, `Healthy`).
   - Derived from `terminal_fallback_fields` in `curation.jsonl`.
   - Indicates policy-defined finality, not correctness.

3. **REPAIRED**
   - Field value was modified by the backend repair loop.
   - Derived from `attempts_by_field` and repair evidence.
   - Indicates value differs from initial LLM proposal.

4. **OVERRIDDEN** (existing)
   - Session override differs from backend value.
   - Takes visual precedence but does not suppress backend badges.

### Badge Rules

- Multiple badges may coexist for a field (e.g. TERMINAL + OVERRIDDEN).
- Badges are **informational only** and never block edits.
- Tooltips must explain:
  - what the badge means,
  - that it reflects backend behavior,
  - that curator overrides remain allowed.

### Visual Placement

- Badges appear inline in the Field Status Dashboard.
- Consistent ordering and iconography across all fields.
- No backend data reordering or mutation.

## Why No Backend Change Is Required

- All signals required already exist in:
  - `curation.jsonl`,
  - `evidence.jsonl`,
  - in-memory override state.
- No new state, schema, or policy is introduced.
- The UI summarizes backend intent; it does not reinterpret it.

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change

## Acceptance Criteria

1. Each field clearly displays its backend state via badges:
   - LOCKED
   - TERMINAL
   - REPAIRED
   - OVERRIDDEN
2. Curators can determine field mutability without opening evidence panels.
3. Overrides remain possible for all fields, regardless of badge state.
4. No JSONL files are modified.
5. Existing UI tests pass or are updated only for badge rendering changes.

## Non-Goals

- No automatic override recommendations.
- No enforcement or blocking of curator edits.
- No backend state inference beyond explicit signals.
- No change to decision semantics.

## Constraints

- Backend output remains authoritative.
- UI must not invent new field states.
- Determinism and auditability must be preserved.

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-102.md` and paste this ticket verbatim.
