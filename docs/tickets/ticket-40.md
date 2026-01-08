# Ticket #40: UI-002 — Evidence + suggestions panels, and widen curation table (Streamlit width deprecation fix)

## Background

Ticket #39 delivered a read-only Streamlit viewer. Curators now need (1) clearer per-GSM evidence and suggestions views, and (2) a usable wide table layout. Also, Streamlit warns that `use_container_width` is deprecated and must be replaced with `width='stretch'` (or `width='content'`).

This ticket adds the evidence/suggestions panels and fixes table width and the deprecation warning.

---

## Scope (STRICT)

### A) Evidence and suggestions panels (per GSM)

**In scope**

1. For the selected `(gse_accession, gsm_accession)`:

   * Display **raw evidence JSON** (pretty-printed JSON).
   * Display **raw suggestions JSON** list (pretty-printed JSON), grouped by `field` when possible.
2. Add a lightweight “summary header” above raw JSON:

   * Evidence: show if evidence exists for this GSM (yes/no).
   * Suggestions: number of suggestions for this GSM (0 if none or file missing).
3. Keep behavior deterministic and read-only.

**Out of scope**

* Any interpretation logic (no scoring, no “apply suggestion”, no auto-fixes)
* Editing any fields
* Exporting overrides

### B) Make the curation table wider and fix Streamlit deprecation

**In scope**

1. Replace all `use_container_width=...` usage with the new API:

   * `width='stretch'` where we want full width
   * `width='content'` otherwise
2. Make the main table clearly wide enough to view all canonical columns:

   * Use page layout `wide`
   * Use a component that supports stretching width (see implementation notes)
3. Ensure the warning disappears.

---

## Implementation notes

### Recommended Streamlit layout changes

1. At app startup:

   * `st.set_page_config(layout="wide")`

2. Prefer a table component that supports `width='stretch'`:

   * If using `st.dataframe`: set `width='stretch'` and also consider `hide_index=True`.
   * If using `st.data_editor` in read-only mode: set `disabled=True` and `width='stretch'`.
   * If using `st.dataframe` and columns are still cramped, explicitly set column configs or use `column_config` to widen key columns (gsm_accession, tissue_type, disease).

3. Replace any occurrence like:

   * `st.dataframe(df, use_container_width=True)`
     with:
   * `st.dataframe(df, width='stretch')`

This must address the warning you saw:

> “Please replace `use_container_width` with `width` … For `use_container_width=True`, use `width='stretch'`."

---

## Acceptance Criteria

### Evidence/Suggestions panel

* Selecting a GSM shows:

  * Evidence raw JSON (or “no evidence record”)
  * Suggestions raw JSON list (or “suggestions not loaded” / “0 suggestions”)
* Grouping by field (if implemented) is correct and deterministic.
* UI remains read-only and does not write files.

### Table width + deprecation fix

* The curation table is displayed in a wide layout and is readable (full set of canonical columns visible without truncation in common desktop widths).
* No `use_container_width` warnings appear when running the app.

---

## Tests Required

No live Streamlit tests. Add/extend pure-function tests:

1. `lookup_evidence(gse,gsm)` returns correct evidence record or `None`.
2. `lookup_suggestions(gse,gsm)` returns list (possibly empty) and can group by field deterministically.
3. (Optional) a simple test that ensures the table rendering call site no longer contains the string `use_container_width` (cheap grep-style test in CI), if your test style allows it.

---

## Non-Goals (Explicit)

* No editing or overrides generation.
* No backend or artifact schema changes.
* No suggestion application logic.

---

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-40.md` and paste this ticket verbatim.
