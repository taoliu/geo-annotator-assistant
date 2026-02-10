# Ticket #151: GSE selector dropdown opens at current selection, not top

## Background

During multi-GSE curation sessions, curators frequently switch between nearby GSEs. The current GSE selector dropdown always opens scrolled to the top of the list, forcing repeated manual scrolling to reach the next GSE.

## Problem Statement

The GSE selector does not preserve navigation context. Each time the dropdown is opened, it resets scroll position to the first GSE, creating unnecessary friction when navigating sequential or nearby GSEs.

## Proposed Change

In the GSE selection dropdown UI:

- When opening the dropdown:
  - Automatically scroll the list so that the **currently active GSE is visible and centered** (or near-centered).
- Highlight the active GSE clearly in the list (existing highlight may be reused).
- No change to sorting order or list contents.

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change (policy-spec.md must be updated)

## Acceptance Criteria

- Opening the GSE dropdown shows the currently active GSE without manual scrolling.
- The user can immediately move up/down to adjacent GSEs.
- Behavior works consistently after switching GSEs multiple times in one session.
- No backend calls or data loading behavior changes.

## Non-Goals

- No changes to how GSEs are discovered or ordered.
- No persistence of scroll position across browser reloads.

## Constraints

- UI-only change.
- Must not trigger additional data fetches or state resets.

## Guiding Principle

**Navigation should preserve context.**

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-151.md` and paste this ticket verbatim.
