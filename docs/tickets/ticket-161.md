# Ticket #161: Reduce unnecessary top whitespace in sidebar and main panel

## Background

The current layout shows significant empty vertical space at the top of:

- The sidebar (above “GSE Selection”)
- The main panel (above the GSE title)

This reduces usable screen space and makes the interface feel less compact.

## Problem Statement

Excessive top padding creates:

- Wasted vertical space
- More scrolling for smaller screens
- Reduced information density

The empty space does not serve a structural or visual separation purpose.

## Proposed Change

Reduce top vertical spacing by adjusting layout padding/margins:

1. Sidebar:
   - Reduce top padding above the first section header.
   - Ensure spacing remains consistent with internal section spacing.

2. Main panel:
   - Reduce top margin above the GSE title.
   - Keep enough space to avoid crowding with browser chrome.

3. Apply spacing consistently:
   - Sidebar and main panel top alignment should feel balanced.
   - Avoid removing all padding; aim for compact but not cramped.

No changes to:

- Section structure
- Typography hierarchy
- Component ordering
- Backend behavior

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change (policy-spec.md must be updated)

## Acceptance Criteria

- Visible reduction in top whitespace in both sidebar and main view.
- No visual overlap with browser UI.
- No layout shifting or clipping.
- Section headers remain readable and properly separated.

## Non-Goals

- No global typography changes.
- No section reordering.
- No removal of structural containers.

## Constraints

- UI-only.
- Must not break responsiveness.
- Must not introduce scroll-jumping.

## Guiding Principle

**Maximize usable space without sacrificing readability.**

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-161.md` and paste this ticket verbatim.
