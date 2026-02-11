# Ticket #157: Improve hover diagnostics readability with key–value visual styling

## Background

Hover tooltips in the curation table expose rich, structured diagnostics (displayed value, backend value, ontology status, flags, etc.). While the content is accurate and complete, it is currently rendered as plain text, which makes scanning and interpretation slower than necessary.

## Problem Statement

The hover diagnostics tooltip presents dictionary-style information as a flat text block. Keys and values are visually indistinguishable, increasing cognitive load and reducing readability during rapid curator review.

## Proposed Change

Redesign the hover diagnostics tooltip for readability, without changing content:

1. Key–value visual separation
   - Render each diagnostic entry as:
     - **Key** (visually emphasized)
     - Value (normal text)
   - Example:
     - **Displayed:** liver
     - **Backend:** liver

2. Key styling
   - Use a subtle colored background or badge-style pill for keys
   - Keys should be visually consistent across all tooltips
   - Suggested (non-binding):
     - light gray or light blue background
     - rounded corners
     - slightly smaller font than values

3. Grouping (optional but recommended)
   - Visually group related fields, for example:
     - Values (Displayed, Backend, LLM original)
     - Ontology (Ontology alternates, status, confidence)
     - Repair / fallback (Attempts, terminal fallback)
     - Evidence (flags)
   - Grouping must be visual only (spacing or divider), not semantic reinterpretation.

4. Color safety
   - Tooltip styling must not conflict with:
     - green override cell background
     - orange flagged cell background
   - Tooltip remains neutral and informational.

No changes to:
- tooltip content
- evidence sources
- flag semantics
- backend behavior

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change (policy-spec.md must be updated)

## Acceptance Criteria

- Hover tooltip content remains identical in meaning and wording.
- Keys are visually distinguishable from values at a glance.
- Tooltip is easier to scan without reading line-by-line.
- Tooltip remains readable on light and dark backgrounds.
- No new information is added or inferred.

## Non-Goals

- No summarization or condensation of diagnostic information.
- No hiding or truncating fields.
- No new severity or confidence indicators.

## Constraints

- UI-only change.
- Tooltip content must continue to be sourced directly from existing diagnostic data structures.
- Must not introduce layout jitter or obscure table cells during hover.

## Guiding Principle

**Clarity without reinterpretation.**  
Diagnostics should be easier to read, not smarter.

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-157.md` and paste this ticket verbatim.
