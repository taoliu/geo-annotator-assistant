# Ticket #38: UI-000 — Define UI contract + JSONL readers (strict, validated)

## Background

v0.4 produces a stable review bundle (`curation.jsonl`, `evidence.jsonl`, `suggestions.jsonl` opt-in) and supports explicit human correction via `overrides.jsonl`, with **no UI yet**. v0.5 begins UI work, but must preserve invariants: **no hidden/persistent state**, deterministic behavior, and no inference or learning. 

This ticket establishes the **UI-side data contract** and implements **robust JSONL readers** that will be reused by all later UI tickets.

---

## Scope (STRICT)

**In scope**

1. Define a **UI-facing normalized record model** for:

   * `curation.jsonl` rows
   * `evidence.jsonl` rows
   * `suggestions.jsonl` rows (optional input; reader must tolerate missing file)
2. Implement JSONL file loaders with:

   * line-numbered parse error reporting (file path + line number + short error)
   * schema validation (required keys, allowed fields)
   * deterministic ordering of loaded records
3. Add unit tests for loaders and ordering.

**Out of scope**

* Any UI rendering (Streamlit/FastAPI/etc.)
* Any write path (no export, no overrides generation)
* Any backend pipeline changes, inference, repair, grounding, or audit changes

---

## Goals

1. Provide a small, stable **UI contract** that later tickets can rely on.
2. Ensure **deterministic, reproducible** loading and ordering.
3. Make failures actionable (exact file + line number) for curators and developers.

---

## UI Contract (v1)

### Canonical field set (must match v0.x outputs)

The UI contract must treat the following as the **only editable/primary fields** in later tickets:

`data_type`, `organism`, `tissue_type`, `cell_line`, `disease`, `treatment`

The UI must also preserve identifiers:

`gse_accession`, `gsm_accession`

### Normalized curation record (UI v1)

A normalized record produced by the loader must include:

```json
{
  "gse_accession": "GSE12345",
  "gsm_accession": "GSM67890",
  "fields": {
    "data_type": "RNA-seq",
    "organism": "Homo sapiens",
    "tissue_type": "Blood",
    "cell_line": "No",
    "disease": "Healthy",
    "treatment": "No"
  },
  "raw": { "...": "original JSON object from curation.jsonl" }
}
```

Rules:

* `fields` must contain **only** the canonical field set above.
* Any extra keys from the source row must be preserved under `raw` (lossless).

### Evidence record (UI v1)

Loader must preserve evidence rows losslessly and extract minimal index keys:

```json
{
  "gse_accession": "GSE12345",
  "gsm_accession": "GSM67890",
  "raw": { "...": "original JSON object from evidence.jsonl" }
}
```

No attempt to interpret evidence content in this ticket (later UI will render it). Evidence is structural diagnostics only. 

### Suggestions record (UI v1)

Same approach:

```json
{
  "gse_accession": "GSE12345",
  "gsm_accession": "GSM67890",
  "field": "disease",
  "raw": { "...": "original JSON object from suggestions.jsonl" }
}
```

* `field` must be one of the canonical editable fields.
* Suggestions are advisory and must remain separate from outputs. 

---

## Ordering and Determinism

Loaders must return deterministic order:

* Curation records: sort by `(gse_accession, gsm_accession)`
* Evidence records: sort by `(gse_accession, gsm_accession)`
* Suggestions records: sort by `(gse_accession, field, gsm_accession)` (match v0.4 suggestion ordering rule)

If any record is missing required keys, raise a validation error.

---

## File-level tasks

Add a new UI package with no dependencies on LLM code paths:

1. `src/ui/__init__.py`
2. `src/ui/schema.py`

   * define canonical field list
   * define lightweight dataclasses / typed dicts (your choice)
3. `src/ui/loaders.py`

   * `load_jsonl(path) -> list[dict]` with line-numbered errors
   * `load_curation_jsonl(path) -> list[NormalizedCurationRecord]`
   * `load_evidence_jsonl(path) -> dict[(gse,gsm)] -> EvidenceRecord` or list, but deterministic
   * `load_suggestions_jsonl_optional(path) -> list[SuggestionRecord]` (missing file allowed)
4. `tests/ui/test_loaders.py`

   * fixtures and tests below

Keep this code isolated from `src/agent/*` to avoid accidental coupling.

---

## Acceptance Criteria

**Functional**

* Loaders can read valid JSONL files and return normalized records.
* Missing `suggestions.jsonl` is handled gracefully (returns empty list + explicit status).

**Correctness**

* Required keys are enforced (`gse_accession`, `gsm_accession`; plus `field` for suggestions).
* Canonical fields enforced in `fields` mapping.
* Extra keys are preserved under `raw` for losslessness.

**Determinism**

* Sorting rules enforced; repeated loads produce identical ordering and identical normalized output.

**Safety**

* No file writes.
* No persistence.
* No LLM calls, no backend pipeline invocation. 

---

## Tests Required

1. **Valid-load test (curation)**

   * Load a small fixture JSONL
   * Assert normalized structure and canonical fields presence

2. **Line-number parse error test**

   * Fixture with one malformed JSON line
   * Assert error message includes file path + failing line number

3. **Missing required keys test**

   * Remove `gsm_accession` from a row
   * Assert validation error (clear message)

4. **Deterministic ordering test**

   * Shuffle fixture input lines
   * Assert output sorted as specified

5. **Optional suggestions missing test**

   * Provide non-existent path
   * Assert empty list and no exception

---

## Non-Goals (Explicit)

* No UI, no CLI, no export, no override generation.
* No data cleaning, ontology validation, synonym logic, or interpretation of evidence.
* No changes to v0.4 artifact writers or schemas.

---

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-38.md` and paste this ticket verbatim.

---
