# Ticket #34: CURATION-002 — Emit `curation.jsonl` as a lossless JSON mirror of `curation.tsv`

### Background

v0.3 already emits `curation.tsv`, which is curator-friendly but not ideal for UI and programmatic review workflows.

v0.4 needs a structured, self-describing per-GSM artifact. However, to avoid schema drift and output mismatches, `curation.jsonl` must be a **lossless, JSON-native mirror** of the existing TSV output.

This ticket adds `curation.jsonl` (one JSON object per GSM) that is derived from the **same source of truth** as `curation.tsv`.

This ticket is **output-only**. No decision logic, repair behavior, ontology grounding logic, or overrides are changed.

---

### Scope (STRICT)

**In scope**

* Emit `curation.jsonl` alongside `curation.tsv`
* Ensure JSONL is a **lossless mirror** of TSV semantics
* Use the same row-building logic as TSV
* JSON-native types for list/dict/int fields

**Out of scope**

* Applying overrides
* UI implementation
* Evidence extraction
* Cross-GSM aggregation / suggestions
* Any changes to pipeline behavior

---

### Goals

1. Provide a structured artifact for UI and downstream tooling
2. Prevent schema drift by mirroring TSV exactly
3. Preserve determinism and auditability
4. Keep existing TSV outputs unchanged

---

### Canonical Field List (MUST MATCH TSV)

`curation.jsonl` records must contain **exactly** the fields in the TSV curation header, in the same naming and semantics:

* `gse_accession`
* `gsm_accession`
* `final_decision`
* `data_type`
* `organism`
* `tissue_type`
* `cell_line`
* `disease`
* `treatment`
* `primary_failure`
* `terminal_fallback_fields`
* `n_llm_calls`
* `attempts_by_field`
* `ontology_status_tissue_type`
* `ontology_status_disease`
* `flags`

No additional fields in this ticket.

---

### Record Structure and Types (JSON-native)

Each line is one JSON object (one GSM). Example:

```json
{
  "gse_accession": "GSE12345",
  "gsm_accession": "GSM67890",
  "final_decision": "ACCEPT",
  "data_type": "RNA-seq",
  "organism": "Homo sapiens",
  "tissue_type": "Liver",
  "cell_line": "No",
  "disease": "Hepatocellular carcinoma",
  "treatment": "None",
  "primary_failure": "",
  "terminal_fallback_fields": ["disease"],
  "n_llm_calls": 4,
  "attempts_by_field": {"disease": 2, "tissue_type": 1},
  "ontology_status_tissue_type": "grounded",
  "ontology_status_disease": "synonym",
  "flags": ["gse_outlier_disease"]
}
```

Type requirements:

* Strings (may be empty): all string fields above
* `terminal_fallback_fields`: list
* `flags`: list
* `attempts_by_field`: object/dict
* `n_llm_calls`: integer

---

### Source of Truth Requirement (MUST)

`curation.jsonl` MUST be derived using the **same row-building logic** as `curation.tsv`.

Implementation must:

* Reuse the existing row builder used for TSV (for example `_build_curation_row(...)`)
* Reuse the canonical column list used for TSV (for example `_CURATION_COLUMNS`)
* Serialize the built row directly to JSON without TSV stringification

Prohibited:

* Recomputing these fields using alternative code paths
* Reformatting or renaming fields
* Nesting fields under `outputs` or `audit`

---

### Output Location and Naming

* Emit `curation.jsonl` in the same output directory where `curation.tsv` is written
* The JSONL filename must be stable and predictable: `curation.jsonl`

---

### Determinism Requirements

* For a fixed input set and fixed config/seed, `curation.jsonl` content must be stable across runs
* If a `run_id` or timestamp exists elsewhere, it must not be injected into `curation.jsonl` in this ticket

---

### Acceptance Criteria

**Functional**

* `curation.jsonl` is produced for runs that produce `curation.tsv`
* One JSON record per GSM (one line per GSM)

**Correctness**

* For each GSM, the JSON record values match TSV semantics exactly
* JSON uses native types for list/dict/int fields (no TSV-style stringification)
* No missing or extra keys relative to the TSV column list

**Compatibility**

* Existing `curation.tsv` output remains unchanged
* Downstream scripts that rely on TSV remain unaffected

---

### Tests Required

1. **TSV/JSON equivalence test (golden)**

   * Run pipeline on fixed inputs
   * Parse `curation.tsv` and `curation.jsonl`
   * Confirm the same number of rows/records
   * For each row/record and each column:

     * Values match after applying the TSV parsing rules for list/dict/int fields

2. **Schema test**

   * Assert exactly the canonical 16 keys exist per record

3. **Determinism test**

   * Run twice with identical inputs/config
   * Ensure `curation.jsonl` is identical byte-for-byte

---

### Non-Goals (Explicit)

* No evidence snippets
* No cross-GSM suggestions
* No overrides application
* No UI

---

### Documentation Updates

* Update `docs/RESUME.md` to mention `curation.jsonl` as a supported output artifact and that it mirrors `curation.tsv`
* No whitepaper update required

---

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-34.md` and paste this ticket verbatim.

---

### Codex working-note (MANDATORY)

At the start of the Codex session:

> **Working on ticket-34**

This note must remain visible in:

* Codex session notes
* Commit messages related to this ticket
