# Ticket #126: UI polish for status header and add persistent curator “checked” column

## Background

With the AG Grid curation table, the status icon column is now the primary entry point
for opening details. The visible “Status” header label is redundant.

Curators also need a simple way to mark that a GSM row has been reviewed (“checked”)
during long sessions. This check state must persist across reloads and be stored on disk.

## Problem Statement

1) The Status column header consumes space and adds visual noise.
2) There is no persistent curator-controlled “reviewed/checked” marker per GSM.
   Curators need an explicit, durable checkbox per row.

## Proposed Change

### A) Remove Status column header text
- For the status icon column, do not display the header text “Status”.
- Keep the column itself and icons unchanged.

### B) Add a persistent “checked” column
Add a new column named `checked` positioned:
- immediately after the Status icon column
- immediately before `gse_accession`

Column behavior:
- Displays a checkbox per row.
- Checkbox is editable directly in the table.
- Default value is unchecked for GSMs with no saved state.

Persistence requirements:
- The checked state must be persisted to disk whenever it changes.
- Persistence must be explicit and auditable as a UI artifact (not backend semantics).

Storage format (new UI artifact):
- Create a new JSONL file under the UI output directory, keyed per GSM:
  - Suggested filename: `checked.jsonl`
  - One record per GSM:
    - `gse_accession`
    - `gsm_accession`
    - `checked` (boolean)
    - `updated_at` (ISO-8601 string, UI timestamp)

Load behavior:
- On UI startup for a GSE, load `checked.jsonl` if present and apply to rows.
- If multiple entries exist for a GSM, last-write-wins by file order (append-only).
- If file missing, treat all rows as unchecked.

UI governance constraints:
- This must not affect backend outputs, decisions, flags, or overrides.
- This is purely a curator workflow aid.

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change (policy-spec.md must be updated)

## Acceptance Criteria

- The Status column header displays no text.
- A new `checked` column exists between Status and `gse_accession`.
- Curators can toggle the checkbox per row.
- Toggling a checkbox writes an update to disk immediately (or within the same rerun),
  and the state is preserved on page reload.
- The checked state is scoped by GSM accession and does not bleed across GSEs.
- No backend artifacts (curation/evidence/audit JSONLs, overrides, final exports) are changed.

## Non-Goals

- Do not use “checked” as an automation signal (no filtering logic required unless
  separately ticketed).
- Do not interpret checked as approval or acceptance.
- Do not modify backend schema or export schema.

## Constraints

- UI-only change.
- Use deterministic file naming and stable append-only writes.
- Ensure concurrency safety is reasonable for single-user curator workflow
  (same assumptions as overrides persistence).

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-126.md` and paste this ticket verbatim.
