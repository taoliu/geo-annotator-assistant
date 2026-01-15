# Ticket #59: UI-UX-002 — Make `gsm_accession` the primary “open details” affordance (styling + guidance + row highlight)

## Background

After Ticket #58, GSM details are shown in a modal popup. However, the current table interaction still appears checkbox-driven (selection column), which is confusing and feels indirect.

We want curators to naturally treat the `gsm_accession` cell as the primary action to open details, even if Streamlit selection mechanics remain in place.

This ticket is UI-only and does not change backend behavior.

---

## Scope (STRICT)

### In scope

1. **Visual affordance for `gsm_accession`**

   * Render the `gsm_accession` column as “clickable” (link-like):

     * underline or link-like styling
     * hover hint text (tooltip) like “Open details”
   * The goal is discoverability, not new behavior.

2. **Inline UI guidance**

   * Add a short, unobtrusive instruction above the curation table:

     Example:

     * “Click a GSM accession to open details.”

   * Optional: add a small expander (“Help”) explaining:

     * how to open/close the details modal
     * that overrides are session-only

3. **Row highlight to reinforce context**

   * When a GSM is selected (modal open or active row set), visually highlight that row in the table (styling only).
   * Highlight must be deterministic and derived only from UI session state.

4. **No interaction redesign**

   * Do not introduce per-row buttons or custom table widgets in this ticket.
   * Do not attempt to replace Streamlit’s selection control column.

---

## Explicitly Out of Scope

* Any changes to selection mechanics beyond styling and guidance
* Any changes to modal content semantics (evidence redesign comes later)
* Backend changes, schema changes, persistence, learning

---

## Implementation Notes (Non-binding guidance)

* Prefer using existing UI styling utilities in `src/ui/styling.py`.
* If full cell-level styling is limited by the chosen Streamlit table widget:

  * apply styling to the entire `gsm_accession` column where possible, and
  * rely on the guidance text + row highlight for the rest.
* Tooltip can be implemented via Streamlit help/label patterns if true hover tooltips are limited.

---

## Acceptance Criteria

1. The UI clearly communicates that `gsm_accession` is the intended entry point for opening the detail modal.
2. The table has a visible row highlight for the active GSM.
3. The instruction text appears above the table and is concise.
4. No backend behavior changes.
5. All tests pass:

```
uv run pytest -q
```

---

## Tests Required

Update or add unit tests under `tests/ui/` to cover:

1. **Guidance presence**

   * The table rendering path includes the instruction/help text.

2. **Active-row styling hook**

   * A unit-testable helper applies a highlight marker/styling based on `active_row_idx` (or active GSM accession).

Tests should avoid requiring a browser session. Refactor styling logic into a pure helper if needed.

---

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-59.md` and paste this ticket verbatim.

---
