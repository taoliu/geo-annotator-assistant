# Ticket #170: Improve tooltip placement to avoid covering values in the same column

## Background

The curation table displays rich diagnostic tooltips on hover. Tooltips are large by design to show values, ontology status, and evidence.

## Problem Statement

Current tooltip placement can overlap and obscure other cells in the same column as the hovered cell (e.g., hovering `cell_line` produces a tooltip that covers other `cell_line` values). This blocks scanning and makes it hard to compare values within the column.

## Proposed Change

Implement deterministic tooltip placement rules to minimize occlusion of the hovered column:

1. Placement preference
   - Default: place tooltip to the **right** of the hovered cell.
   - If insufficient space on the right: place tooltip to the **left** of the hovered cell.
   - If neither side has sufficient space: place tooltip **below** (or above) as a fallback.

2. Alignment
   - Align tooltip top edge with the hovered cell row (or slightly offset).
   - Add a small gap so the tooltip does not touch the cell border.

3. Viewport safety
   - Tooltip must remain fully within the viewport (no clipping off-screen).
   - If needed, constrain max width and allow wrapping.

4. Interaction
   - Tooltip should remain readable and stable while hovering (no jitter).
   - Tooltip must not interfere with click-to-edit behavior.

No changes to tooltip content.

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change (policy-spec.md must be updated)

## Acceptance Criteria

- Hovering a cell shows the tooltip without covering most values in the same column in typical layouts.
- Tooltip placement prefers the side with available space.
- Tooltip never renders off-screen.
- Behavior is consistent across columns and scroll positions.
- Tooltip content is unchanged.

## Non-Goals

- No reduction of tooltip content.
- No new diagnostic fields.
- No changes to backend semantics.

## Constraints

- UI-only.
- Must work for large tooltips and narrow windows.
- Must not rely on brittle CSS selectors that break on minor Streamlit updates.

## Guiding Principle

**Tooltips should inform without obstructing comparison.**

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-170.md` and paste this ticket verbatim.
