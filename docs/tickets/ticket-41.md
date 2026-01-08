# Ticket #41: UI-003 — Field-level flag extraction + highlighting (read-only)

## Background

We now have a usable read-only viewer (tickets 39–40). Curators need to quickly see which GSMs and which fields are problematic. Evidence already contains structural diagnostics, so the UI can highlight flagged fields without any inference or persistence.

This ticket adds **deterministic flag extraction** from `evidence.jsonl` and **cell-level highlighting** in the curation table.

---

## Scope (STRICT)

**In scope**

1. Implement `extract_field_flags(evidence_raw) -> dict[field, list[str]]`:

   * Returns a mapping from canonical field name to a list of flag tags (short strings).
   * Only uses existing evidence content, no new inference.
2. Build an index:

   * `flags_by_gsm[(gse_accession, gsm_accession)] -> set(fields)` (and optionally tags per field)
3. Table highlighting:

   * For each row, highlight the cells for flagged fields.
   * Also highlight the whole row lightly if any field is flagged (optional).
4. Details panel:

   * Show a compact “Flags” section listing flagged fields and their tags.
5. Determinism:

   * The same evidence input yields the same flags and the same highlights.

**Out of scope**

* Editing fields
* Exporting overrides
* Changing evidence generation
* Any “severity scoring” beyond simple tag display

---

## Flagging rules (conservative)

* Canonical fields: `data_type`, `organism`, `tissue_type`, `cell_line`, `disease`, `treatment`.
* Only mark a field as flagged if evidence has an explicit signal for that field.
* If no explicit per-field signal can be found, do not flag it.

Implementation must document exactly which evidence keys/patterns are used. Keep it small and easy to adjust.

---

## Implementation notes

* Add `src/ui/flags.py`:

  * `build_flags_index(evidence_records) -> flags_by_gsm`
  * `extract_field_flags(evidence_raw) -> dict[field, list[str]]`
* Add `src/ui/styling.py`:

  * `style_curation_table(df, flags_by_gsm) -> pandas.io.formats.style.Styler`
* In the Streamlit app:

  * Use `st.dataframe(styler, width='stretch')` (still wide layout)
  * Ensure no deprecated `use_container_width`.

---

## Acceptance Criteria

* A GSM with evidence-indicated issues shows highlighted cells for the impacted fields.
* The details panel lists the same flagged fields and tags.
* GSMs with no issues show no highlighting.
* No file writes, no persistence, no backend calls.

---

## Tests Required

1. Unit tests for `extract_field_flags`:

   * Given a known evidence fixture, assert flagged fields match expectation.
2. Determinism test:

   * Shuffled evidence input yields identical `flags_by_gsm`.
3. Styling test (lightweight):

   * Assert that the styler marks expected cells (test via generated HTML contains expected selectors/markers, or keep it minimal by testing the style map function).

---

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-41.md` and paste this ticket verbatim.
