# Ticket #42: UI-004 — Enable editing + in-memory overrides set (no writes)

## Background

Tickets 39–41 provide a read-only curator UI plus field-level flag highlighting. Next, we allow curators to **edit canonical GSM fields** in the UI, but still keep the system safe:

* **Read-only by default**
* **No file writes in this ticket**
* All edits are **in-memory only** and disappear when the session ends
* No inference, no persistence, no learning

This ticket prepares the edit workflow and the internal override representation that ticket #43 will export as `overrides.jsonl`.

---

## Scope (STRICT)

**In scope**

1. Add an explicit UI control to switch into edit mode:

   * A checkbox or toggle: **“Enable editing”** (default OFF)
   * When OFF: UI is fully read-only as before
2. In edit mode, allow editing of **only** canonical fields:

   * `data_type`, `organism`, `tissue_type`, `cell_line`, `disease`, `treatment`
3. Maintain an **in-memory overrides set** keyed by:

   * `(gse_accession, gsm_accession, field) -> value`
4. Provide minimal edit workflow:

   * When a GSM is selected, show input widgets for those fields
   * “Save changes” applies edits to the in-memory overrides map (not to disk)
   * “Revert this GSM” clears overrides for the selected GSM
   * “Clear all edits” clears all overrides in memory
5. Visual indicators:

   * In the table, show an “edited” marker per row if any overrides exist for that GSM
   * In the details panel, show the current overrides for that GSM (exact values)

**Out of scope**

* Exporting `overrides.jsonl` (next ticket)
* Applying overrides to re-render the entire table as if they were ground truth (optional later; for now we can show “effective value” only in the selected record panel)
* Any validation beyond basic type checks (string/list) and allowed-field enforcement

---

## Data model

Define a minimal override entry in code (not file) as:

```python
OverrideKey = tuple[str, str, str]  # (gse_accession, gsm_accession, field)
OverrideValue = str | list[str]     # match existing field types
```

Rules:

* `field` must be one of the canonical editable fields.
* Values must be JSON-serializable.
* No timestamps, no hidden metadata, unless explicitly requested later.

---

## UI behavior (expected)

### Default state (read-only)

* Edit widgets hidden or disabled.
* No override state created.

### Edit mode ON

* For selected GSM:

  * show each field with current value (from curation record)
  * curator edits value
  * on “Save changes”, store overrides in memory
* Table displays:

  * original curation values
  * plus an “Edited” column (boolean or icon)
  * (optional) if feasible: show overridden values in-place, but only if it is trivial and deterministic

### Safety

* No writes to disk.
* No background autosave.
* Closing the app loses edits.

---

## Implementation notes (Streamlit)

* Use `st.session_state` to store overrides **in memory** for the session.
* Keep the override logic in pure functions so we can test it:

  * `apply_overrides_to_record(record, overrides_for_gsm) -> effective_fields`
  * `set_override(overrides, key, value) -> overrides`
  * `clear_overrides_for_gsm(overrides, gse, gsm) -> overrides`
* Ensure row “edited” markers are derived solely from the override map.

---

## Acceptance Criteria

* Edit mode is OFF by default; UI remains read-only unless explicitly enabled.
* In edit mode, curator can change canonical fields and save them to the in-memory override set.
* UI shows clear indicators of which GSMs have edits.
* Revert (per GSM) and clear-all work.
* No file writes occur.
* No deprecated Streamlit parameters introduced.

---

## Tests Required

1. `set_override` / `clear_overrides_for_gsm` / `clear_all` unit tests.
2. `apply_overrides_to_record` unit tests:

   * override one field
   * override multiple fields
   * override with list values
3. Determinism test:

   * overrides applied in different order yield identical effective record output.

---

## Non-Goals (Explicit)

* No `overrides.jsonl` export in this ticket.
* No server-side persistence, no DB.
* No suggestion auto-application.

---

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-42.md` and paste this ticket verbatim.
