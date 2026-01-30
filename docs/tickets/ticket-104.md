# Ticket #104: GSE-Level Triage and Prioritization Dashboard Enhancements

## Background

As of v0.9, the backend emits richer GSM-level outcomes and GSE post-pass
diagnostics, which are already reflected in `curation.jsonl` and
`evidence.jsonl`. In large GSEs, however, the current Curator UI (v0.7) treats
all GSMs as visually equivalent in the main table.

This makes it difficult for curators to quickly identify:
- GSMs that most urgently require attention,
- systematic issues affecting many GSMs in a GSE,
- outliers surfaced by backend diagnostics.

This is a workflow prioritization issue, not a backend limitation.

## Problem Statement

The current GSM table supports basic navigation but does not support effective
triage under v0.9 policy density.

Specifically:
- FLAGGED GSMs are not meaningfully prioritized beyond a single status column.
- GSE-level outlier signals are not surfaced as first-class triage cues.
- Curators must scan many rows to identify common failure patterns.
- Review effort does not scale well with GSE size.

## Proposed Change (UI Only)

Enhance the GSE-level view with **read-only triage signals and controls**,
derived entirely from existing backend artifacts.

### Inputs (Read-Only)

- `curation.jsonl`
  - `final_decision`
  - `primary_failure`
  - `flags`
- `evidence.jsonl`
  - GSE post-pass diagnostics
  - field-level grounding and repair metadata
- `suggestions.jsonl` (optional, advisory only)

### UI Enhancements

1. **Triage Indicators in GSM Table**

Add non-intrusive visual indicators per GSM row, such as:
- FLAGGED vs ACCEPT emphasis
- presence of ambiguous flags
- presence of terminal fallbacks
- presence of session overrides

These indicators are purely descriptive and do not alter sorting by default.

2. **Triage-Oriented Sorting and Filtering**

Provide optional UI controls to:
- sort GSMs by:
  - final decision,
  - number of ambiguous fields,
  - presence of primary failures,
  - presence of overrides
- filter GSMs by:
  - decision state (ACCEPT / FLAGGED),
  - specific primary failures,
  - specific flags

All filters are client-side and reversible.

3. **GSE-Level Summary Panel**

Add a compact, read-only summary panel showing:
- total GSM count,
- number and fraction of FLAGGED GSMs,
- most common primary failures,
- most common flags,
- count of GSMs with overrides (session-only).

4. **Outlier Emphasis**

If GSE post-pass diagnostics indicate outliers:
- visually mark affected GSMs,
- surface the outlier category in the summary panel.

No new aggregation logic is introduced beyond counting and grouping.

## Why No Backend Change Is Required

- All required signals already exist in:
  - `curation.jsonl`,
  - `evidence.jsonl`,
  - optional `suggestions.jsonl`.
- The UI performs only client-side grouping and display.
- No inference, propagation, or reinterpretation of backend decisions occurs.

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change

## Acceptance Criteria

1. Curators can visually identify high-priority GSMs in large GSEs without
   opening each modal.
2. Sorting and filtering are reversible and do not mutate backend data.
3. GSE-level summary accurately reflects underlying JSONL content.
4. No JSONL files are modified or extended.
5. UI remains strictly read-only with respect to backend semantics.

## Non-Goals

- No automatic review ordering or recommendations.
- No cross-GSM inference or normalization.
- No backend aggregation logic.
- No persistence of triage state.

## Constraints

- Backend outputs remain authoritative.
- UI must not invent new analytical signals.
- Determinism and auditability must be preserved.

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-104.md` and paste this ticket verbatim.
