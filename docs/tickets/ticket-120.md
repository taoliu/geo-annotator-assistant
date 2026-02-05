# Ticket #120: Replace curation table with AG Grid to enable status-cell click and rich hover tooltips

## Background

The current Streamlit-based curation table requires checkbox/row-selection behavior to open
the GSM detail modal. This is counterintuitive for curators, who expect to click the status
indicator (flag/check) directly.

In addition, curators need richer per-cell inspection via hover, including backend values,
LLM raw values, and ontology candidate alternates when available.

Streamlit core tables do not provide reliable per-cell click events or rich tooltips.

## Problem Statement

The curation table interaction model is inefficient:
- The modal open gesture is not aligned with curator expectations.
- There is no per-cell hover inspection for backend vs LLM vs ontology alternates.
- Adding these behaviors using Streamlit core components is not feasible without hacks.

## Proposed Change

Replace the Streamlit curation table component with an AG Grid-based table (via
`streamlit-aggrid` or an equivalent vetted AG Grid wrapper), while preserving
all existing UI semantics and backend authority boundaries.

### 1) Status-cell click opens details modal
- The `Status` column renders the existing status icon (flag/check).
- Clicking a cell in the `Status` column triggers opening the GSM detail modal
  for that row.
- Clicking other cells should NOT open the modal by default (unless explicitly
  configured as a follow-up ticket).

### 2) Rich hover tooltips for inspector transparency (read-only)
For cells in the 8 canonical fields, display a tooltip that includes (when available):

- Current displayed value (post-override if applicable)
- Backend-derived value (pre-override)
- LLM raw proposed value (from audit artifacts)
- Ontology alternates / match candidates (only if already present in existing
  audit/evidence/suggestions artifacts; do not re-run grounding)

Tooltips must be read-only visualizations. No inference or recomputation is introduced.

### 3) Preserve existing behaviors
- Quick filters (All / Needs attention / Has overrides / Clean)
- Flag-based cell highlighting
- GEO links for GSE/GSM accessions
- Override editing and persistence behavior
- Export behaviors (JSONL and CSV tickets, if implemented)

### 4) UI governance constraints (must hold)
- Backend outputs remain the source of truth.
- UI must not re-run backend validation/repair/grounding.
- No schema changes.
- Tooltips and interactions must not reinterpret flags or change decisions.

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change (policy-spec.md must be updated)

## Acceptance Criteria

- The curation table renders using AG Grid.
- Clicking the status icon cell (flag/check) opens the GSM details modal
  for that row reliably.
- Hover tooltips appear on biology fields and show backend vs LLM vs ontology
  info when present in artifacts.
- No backend runs are triggered by UI interactions.
- Overrides continue to persist identically to current behavior.
- Existing UI tests are updated or replaced with AG Grid-compatible tests.

## Non-Goals

- Do not add new backend artifacts or modify existing JSONL schemas.
- Do not introduce new ontology retrieval or grounding calls from the UI.
- Do not implement multi-user editing or collaboration features.
- Do not implement cross-GSM propagation or bulk inference.

## Constraints

- Prefer minimal, incremental migration: replace only the table component first.
- Keep deterministic display ordering and stable column definitions.
- Tooltip content must be sourced only from already-loaded artifacts.

## Guiding Principle

Curator trust and audit transparency must improve, without expanding UI authority.

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-120.md` and paste this ticket verbatim.
