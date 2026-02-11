# Ticket #164: Tighten vertical spacing between top expanders to improve information density

## Background

The top section of the main panel contains multiple expanders (e.g., “Input details”, “GSE-wide biology”, “GSE-wide counts”). While useful, these expanders are currently separated by relatively large vertical gaps.

## Problem Statement

Excess vertical spacing between expanders:

- Reduces usable screen height for the curation table.
- Creates visual fragmentation.
- Makes the interface feel less compact than necessary.

This spacing does not add structural clarity and can be safely reduced.

## Proposed Change

Adjust UI spacing for the expander section:

1. Reduce vertical margin between adjacent expanders.
2. Slightly reduce padding inside collapsed expander headers.
3. Maintain sufficient spacing to preserve readability and click targets.
4. Do not alter expander functionality or content.

No changes to:

- Expander titles
- Expander content
- Default expanded/collapsed behavior
- Backend data or summaries

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change (policy-spec.md must be updated)

## Acceptance Criteria

- Noticeably reduced vertical gaps between expanders.
- No clipping or overlap of expander content.
- Expand/collapse animations behave normally.
- Layout remains responsive across screen sizes.

## Non-Goals

- No removal of any expander.
- No change to summary content.
- No typography changes.

## Constraints

- UI-only.
- Must not rely on brittle CSS selectors that may break on minor Streamlit updates.
- Must not interfere with expander click area.

## Guiding Principle

**Reduce empty space without reducing clarity.**

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-164.md` and paste this ticket verbatim.
