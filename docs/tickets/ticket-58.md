# Ticket #58: UI-UX-001 — Open GSM record details in a modal on table click (remove dropdown + bottom details)

## Background

The current curator UI requires the curator to:

1. select a GSM via a dropdown above the curation table, and
2. scroll to the bottom of the page to view “Record Details”.

This is not user-friendly. It breaks context, forces unnecessary scrolling, and makes row-by-row review slow.

We want the table to be the primary surface. When the curator clicks a GSM accession in the table, the record details must appear in a **pop-up modal** (not rendered below the table).

---

## Scope (STRICT)

### In scope

1. **Remove the dropdown-based GSM selector**

   * Remove (or deprecate from the UI) the “Select GSM” dropdown used to choose which record’s details to display.
   * Selection must be driven by interaction with the curation table.

2. **Replace the bottom-of-page “Record Details” with a modal**

   * Do not render record detail content underneath the table.
   * When the curator selects a GSM from the table, open a modal that shows that GSM’s details.

3. **Click/selection behavior**

   * Primary interaction: selecting a GSM by clicking the GSM accession cell in the gsm_accession column or the GSE accession cell in the gse_accession column.
   * The modal must open for the selected GSM and display the correct detail content.
   * The curator must be able to close the modal and return to the table without losing scroll position.

4. **Modal contents**
   The modal should show the same information currently shown in “Record Details” (no new semantics), including:

   * the 8-field record values
   * evidence presence indicators
   * any existing diagnostic/evidence blocks already displayed today
   * editing controls only if “Enable editing” is checked

   This ticket is a layout + interaction refactor only. Do not add new evidence types or new backend logic.

5. **Session-only edits and overrides export remain unchanged**

   * The override/export section stays on the main page.
   * Editing performed inside the modal must update the same session-only state and be reflected in:

     * the “Edited” column (if present)
     * override counts
     * export preview/output

6. **Implementation constraints**

   * UI-only changes in `src/ui/` (for example `src/ui/app_streamlit.py`, `src/ui/state.py`, `src/ui/styling.py`).
   * No backend pipeline changes.
   * No schema changes.
   * No persistence.

---

## Explicitly Out of Scope

* Any change to backend semantics, validators, ontology grounding, repair logic, or RAG behavior
* New persistence or saving behavior
* Any new fields beyond the existing 8 output fields
* “Evidence redesign” (that will be handled in later UI tickets)

---

## Implementation Notes (Non-binding guidance)

* Prefer Streamlit-native modal primitives if available (for example `st.dialog`).
* If true cell-click is not supported by the current table widget, use the most direct supported mechanism:

  * single-row selection via the table widget, treating “select row” as the click action, while keeping GSM accession visually emphasized as the primary affordance.
* Keep the curation table performant for hundreds+ rows. Do not render one button per row.

---

## Acceptance Criteria

1. The UI no longer requires a dropdown to select the active GSM record.
2. Clicking/selecting a GSM in the curation table opens a modal containing that GSM’s details.
3. No “Record Details” block is shown underneath the curation table.
4. Closing the modal returns focus to the table without disrupting session state.
5. If editing is disabled, the modal is read-only.
6. If editing is enabled, edits in the modal update the same session-only overrides state and are reflected in the export section exactly as before.
7. All tests pass:

```
uv run pytest -q
```

---

## Tests Required

Add or update UI tests under `tests/ui/` to cover:

1. **Selection → modal open state**

   * Selecting a GSM sets the correct “active GSM” state and triggers modal-open state.

2. **Modal content binding**

   * The modal detail renderer displays the correct record given the active GSM.

3. **No bottom details block**

   * The previous “Record Details” renderer is not invoked in the main page flow (structure-level test via refactored functions, not screenshot tests).

Tests must be deterministic and should avoid requiring an actual Streamlit browser session. Refactor state/renderer helpers as needed to make them unit-testable.
