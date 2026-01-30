# Ticket #108: Modernize Curator UI Layout and Reduce Visual Text Density (UI-Only Redesign)

## Background

After v0.9, records include more flags, evidence, and policy signals. The UI is
currently functional but visually dense and text-heavy, which slows review and
reduces curator trust.

## Problem Statement

The UI feels plain and busy:
- too many raw strings shown at once
- limited visual hierarchy
- weak separation between “primary decision signals” and “deep evidence”
- users must read long text blocks instead of scanning

This is a UX presentation issue only.

## Proposed Change (UI Only)

### 1) Establish a Clear Visual Hierarchy

In the GSM detail modal, reorganize into 3 tiers:

- Tier A: decision summary
  - final_decision, primary_failure, key flag groups (from Ticket #101)
- Tier B: field status dashboard
  - compact field list with badges (Ticket #102) and tooltips (Ticket #103)
- Tier C: deep evidence (collapsible)
  - ontology match details, alternates, repair history, etc.

### 2) Collapse / Tooltip Strategy

- Move long explanations into tooltips or collapsible sections.
- Default to compact mode; expand on demand.
- Keep all information accessible (nothing hidden permanently).

### 3) Clean Table Presentation

- Improve spacing, typography, and alignment in the GSM table.
- Make key status signals scannable:
  - decision state
  - primary failure (short label)
  - count of flags or a compact severity indicator

### 4) Navigation and “Less Noise” Defaults

- Add sensible defaults:
  - show summary first, evidence collapsed
  - show only top-N flags in-line with “show more”
- Ensure power users can expand everything.

### 5) Documentation Note

Add a brief note to `docs/ui.md` describing:
- the summary-first layout
- collapsible evidence design
- that UI remains non-authoritative and read-only

## Why No Backend Change Is Required

This is purely presentation and client-side interaction design using existing
`curation.jsonl`, `evidence.jsonl`, `suggestions.jsonl`, and optional `audit.jsonl`.

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change

## Acceptance Criteria

1. The UI presents a clear summary-first experience with reduced text density.
2. Detailed evidence remains available via expand/collapse and tooltips.
3. No backend calls or schema changes are introduced.
4. Existing ticketed behaviors remain intact:
   - #101 flag tiers
   - #102 field badges
   - #103 tooltips
   - #105 override diff
   - #106 LLM original (if enabled)
5. `docs/ui.md` includes a short description of the redesigned layout.

## Non-Goals

- No changes to validation/repair logic or decisions.
- No new inference or recommendations.

## Constraints

- Preserve determinism and auditability.
- UI must not imply that ontology confidence equals correctness.

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-108.md` and paste this ticket verbatim.
