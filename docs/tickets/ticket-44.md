# Ticket #44: UI-006 — Export `overrides.jsonl` (explicit, deterministic, preview-first)

## Background

Tickets 42–43 introduced in-memory overrides via form-based and inline table editing. The final required step for a complete v0.5 curator workflow is to **explicitly export** those edits as `overrides.jsonl`, which the existing v0.4 backend already understands.

This ticket adds **export only**. It must remain explicit, deterministic, previewable, and side-effect free unless the user confirms the export.

---

## Scope (STRICT)

**In scope**

1. Build a deterministic exporter that converts the in-memory overrides map into `overrides.jsonl`.
2. Add a UI section for export:

   * Preview the exact JSONL lines that will be written
   * Explicit “Export overrides” action
3. Enforce a minimal, backend-compatible schema.
4. Do not write anything unless the user explicitly triggers export.

**Out of scope**

* Applying overrides to backend pipelines
* Auto-saving or background writes
* Versioning, timestamps, or curator identity (unless already required by backend)

---

## `overrides.jsonl` schema (v0.5)

Each line must be a standalone JSON object with **exactly** these required keys:

```json
{
  "gse_accession": "GSE12345",
  "gsm_accession": "GSM67890",
  "field": "disease",
  "value": "Healthy"
}
```

Rules:

* `field` must be one of:
  `data_type`, `organism`, `tissue_type`, `cell_line`, `disease`, `treatment`
* `value` must be JSON-serializable and match existing backend expectations (string or list).
* No extra keys by default (keep minimal to avoid backend redesign).

---

## Deterministic ordering (MANDATORY)

Export order must be stable and reproducible:

1. Sort by `gse_accession`
2. Then by `gsm_accession`
3. Then by `field` (lexicographic)

Given the same edits, the output file must be byte-for-byte identical.

---

## UI behavior

### Export section

Add a clearly labeled section, for example:

**Overrides export (session-only edits)**

* Show counts:

  * Edited GSMs: N
  * Edited fields: M
* Show a scrollable **preview**:

  * Exact JSONL lines, in export order
* Buttons:

  * `Export overrides.jsonl`
  * `Cancel / Clear edits` (optional, but recommended)

### File writing

* On click, prompt for a save location (Streamlit download or local save depending on setup).
* Do not overwrite existing files silently.
* After successful export:

  * Show a success message
  * Keep overrides in memory (do not auto-clear unless user chooses)

---

## Implementation notes

1. Add a pure function:

   ```python
   def overrides_to_jsonl(overrides_map) -> list[str]:
       ...
   ```

   * Input: in-memory overrides map
   * Output: list of JSON strings, already sorted
2. UI calls this function to:

   * Render preview
   * Write file on confirmation
3. Reuse canonical field list from Ticket #38 schema to validate `field`.

---

## Acceptance Criteria

* Exported file strictly matches the defined schema.
* Ordering is deterministic.
* Preview matches the written file exactly.
* No file is written unless user explicitly clicks export.
* No backend code paths are touched.

---

## Tests Required

1. Unit tests for `overrides_to_jsonl`:

   * single override
   * multiple overrides across GSMs
   * ordering correctness
2. Validation test:

   * invalid field name raises error
3. Determinism test:

   * same overrides map yields identical JSONL output across runs

---

## Non-Goals (Explicit)

* No backend invocation.
* No automatic override application.
* No persistence beyond explicit export.

---

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-44.md` and paste this ticket verbatim.

---
