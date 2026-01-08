# Ticket #39: UI-001 — Streamlit app scaffold (read-only by default)

## Background

Ticket #38 establishes strict JSONL loaders + a UI-side contract for `curation.jsonl`, `evidence.jsonl`, and optional `suggestions.jsonl`. Now we need the first usable local curator UI: a **read-only** viewer that loads artifacts and displays a searchable table, with zero writes and no persistence. This is the v0.5 UI “hello world” that curators can run locally.

---

## Scope (STRICT)

**In scope**

1. Add a **Streamlit** app that:

   * loads `curation.jsonl` (required)
   * loads `evidence.jsonl` (required)
   * loads `suggestions.jsonl` (optional)
     using the loaders from Ticket #38.
2. Present a **read-only** main table:

   * One row per GSM (`gse_accession`, `gsm_accession`, plus canonical fields)
   * Stable ordering (already ensured by loaders)
3. Add basic navigation:

   * Filter by `gse_accession` (dropdown or text)
   * Free-text search over `gsm_accession` and field values
4. Add a single “record details” panel that displays **raw JSON** for the selected GSM:

   * raw curation object
   * raw evidence object
   * raw suggestions list (if any)

**Out of scope**

* Editing any fields
* Exporting overrides
* Any backend pipeline run / inference / repair
* Any persistence beyond the current browser session
* UI polish beyond basic layout and filtering

---

## Design constraints

* **Read-only by default** and no file writes.
* No hidden persistence: do not write caches, do not create local DB files.
* Deterministic behavior: same inputs, same displayed ordering.
* UI must work even if `suggestions.jsonl` is missing (display “not loaded”).

---

## UX requirements (minimal)

### Layout

* Left: Filters (GSE selector + search box)
* Center: Table of records (curation rows)
* Right or below: Details panel (raw JSON)

### Selection behavior

* Select a GSM row (single selection).
* Details panel updates to show raw objects.

If Streamlit table selection is awkward, it is acceptable to use:

* a `selectbox` keyed by `(gse_accession, gsm_accession)` after filters, plus a table display.

---

## CLI / entrypoint

Add a CLI entry such as:

* `geo-gsm-ui --input-dir <DIR>`

Where `<DIR>` contains:

* `curation.jsonl`
* `evidence.jsonl`
* `suggestions.jsonl` (optional)

Behavior:

* Validate presence of required files.
* Start Streamlit app.
* Show the resolved file paths somewhere in the UI header.

Implementation notes:

* Prefer `python -m streamlit run ...` wrapped by a small console script that passes `--input-dir` through environment variables or Streamlit args.
* Keep everything local.

---

## File-level tasks

1. Add Streamlit dependency (if not already present) in the project’s standard dependency mechanism.
2. New module(s):

   * `src/ui/app_streamlit.py` (or `src/ui/streamlit_app.py`)
   * `src/ui/cli.py` for `geo-gsm-ui`
3. Wire console script entrypoint (project-specific style).
4. Add minimal docs:

   * `docs/ui.md` (or update an existing doc location) with how to run.

---

## Acceptance Criteria

**Functional**

* Running `geo-gsm-ui --input-dir <DIR>` opens a local UI and shows the curation table.
* Filters reduce the table rows deterministically.
* Selecting a GSM shows raw curation/evidence/suggestions JSON.

**Robustness**

* If `suggestions.jsonl` is missing: UI still runs and indicates suggestions are not loaded.
* Loader errors are shown with file path + line number (from Ticket #38).

**Safety**

* No file writes.
* No persistence beyond session memory.
* No backend pipeline calls and no LLM calls.

---

## Tests Required

Unit tests (no live Streamlit server required):

1. `parse_args` / CLI tests:

   * missing `--input-dir` error
   * missing required files error message

2. “UI state builder” tests (factor data prep into a pure function):

   * given loaded records + filter + search string, returns expected subset
   * deterministic ordering preserved

Keep Streamlit rendering itself untested; test the pure logic that prepares the displayed dataset and selected record lookup.

---

## Non-Goals (Explicit)

* No editing, no override export, no suggestion application.
* No authentication, no multi-user support.
* No persistence layer, no SQLite, no caches on disk.

---

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-39.md` and paste this ticket verbatim.
