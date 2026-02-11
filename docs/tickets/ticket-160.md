# Ticket #160: Improve sidebar layout for Filters and Triage (space and scanability)

## Background

The sidebar contains both Filters (GSE, Search) and Triage (Decision, Primary failures, Flags, Sort). As more controls are added, the sidebar becomes harder to scan and takes more vertical space than necessary.

## Problem Statement

Current sidebar layout has several usability issues:

- Controls have similar visual weight, so the eye does not quickly find the most-used items.
- Related controls are not grouped tightly enough.
- Some labels are redundant or could be moved to tooltips.
- “Sort descending” and “Debug table wiring” are visually mixed with triage filters.

## Proposed Change

Redesign the sidebar layout for clarity and compactness (UI-only):

1. Grouping and spacing
   - Use tighter grouping within sections and stronger separation between sections.
   - Reduce unnecessary vertical whitespace between label and widget.

2. Filters section
   - Keep “Search” directly under GSE selector.
   - Optional: add a small tooltip explaining what Search matches (accessions and/or field text), without changing behavior.

3. Triage section
   - Group triage filters (Decision, Primary failures, Flags) together.
   - Group sorting controls (Sort by, Sort descending) under a “Sort” subheader or divider.

4. Debug controls
   - Move “Debug table wiring” under a collapsible “Advanced” or “Debug” subsection so it is not in the main curator path.

No changes to filter semantics, defaults, or backend behavior.

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change (policy-spec.md must be updated)

## Acceptance Criteria

- Sidebar is visually easier to scan (Filters, Triage, Sort, Advanced/Debug).
- Debug checkbox is not in the main flow by default (collapsed or clearly separated).
- No change to what filtering or sorting does.
- All existing selections remain functional.

## Non-Goals

- No new filters.
- No changes to filtering logic.
- No persistence changes beyond existing session behavior.

## Constraints

- UI-only.
- Must not introduce ambiguity about what is being filtered.

## Guiding Principle

**Make common paths obvious; hide rare controls.**

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-160.md` and paste this ticket verbatim.
