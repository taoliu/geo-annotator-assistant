# Ticket #148: Move static instructional text into hover tooltips and info icons

## Background

The UI contains several blocks of static explanatory text (e.g., table legends, bulk edit explanations). While precise and correct, this text is visually busy and repeated across sessions, especially for experienced curators.

## Problem Statement

Persistent instructional text increases visual clutter and reduces information density without providing new value after initial learning.

## Proposed Change

- Replace long-form static instructional text with:
  - small info icons (ⓘ) or help markers
  - hover tooltips containing the existing text verbatim
- Target areas include:
  - curation table legend (“Status: row state…”, “Edited: pencil indicates…”)
  - bulk edit explanatory paragraph
  - hover instructions like “Hover cells for diagnostics…”

No wording changes are required; only relocation.

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change (policy-spec.md must be updated)

## Acceptance Criteria

- Static instructional paragraphs are no longer always visible.
- Hovering over the corresponding info icon reveals the same explanatory text.
- Tooltips are readable, non-obstructive, and do not block table interaction.
- First-time users can still discover guidance without external documentation.

## Non-Goals

- No rewriting or simplifying of instructional text.
- No removal of guidance content.
- No modal dialogs for help.

## Constraints

- Tooltips must not interfere with cell hover diagnostics.
- UI behavior must remain accessible and keyboard-friendly where possible.

## Guiding Principle

**Teach once, then get out of the way.**

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-148.md` and paste this ticket verbatim.
