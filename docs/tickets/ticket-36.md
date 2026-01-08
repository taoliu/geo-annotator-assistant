# Ticket #36: CURATION-004 — Apply overrides deterministically (explicit input, full audit)

### Background

v0.4 introduces human-in-the-loop curation. To preserve determinism and auditability, human edits must be applied only via an explicit input file (`overrides.jsonl`) and must never trigger new inference.

Ticket-33 defined the `overrides.jsonl` schema and loader. This ticket wires that into the pipeline so overrides can be applied **deterministically** at a single well-defined point, with full provenance recorded in the audit.

This ticket must not change behavior when no overrides are provided.

---

### Scope (STRICT)

**In scope**

* Add optional CLI/config support to provide `overrides.jsonl`
* Load and validate overrides using the loader introduced in Ticket-33
* Apply overrides deterministically to final outputs
* Record all applied overrides in audit (provenance)
* Update curation outputs to reflect overrides (TSV + JSONL)

**Out of scope**

* UI implementation
* Any new LLM calls
* Cross-GSM aggregation
* Ontology validation of override values
* Persistence beyond reading the overrides file

---

### Goals

1. Human corrections become an explicit, repeatable input
2. Pipeline remains deterministic
3. Overrides are applied without changing inference behavior
4. Audits clearly show what was overridden and why (if provided)

---

### Override Application Rules

1. **Override timing (MUST)**

   * Apply overrides **after** deterministic repairs and ontology grounding are complete
   * Apply overrides **immediately before** writing final outputs and curation files
   * Do not re-run any repairs or grounding after overrides

2. **Override targeting**

   * Overrides are keyed by `(gsm_accession, field)`
   * `field` must be one of the canonical output fields:

     * `data_type`, `organism`, `tissue_type`, `cell_line`, `disease`, `treatment`
   * Overrides must only affect the **final output** fields

3. **No behavior change without overrides**

   * If no overrides file is provided, outputs must be byte-identical to current behavior

4. **Duplicate overrides**

   * Must already be rejected by loader (Ticket-33). This ticket assumes loader enforces this.

5. **Type handling**

   * Apply the `new_value` exactly as provided by the loader normalization
   * No ontology validation or synonym mapping in this ticket

---

### Audit Requirements (MANDATORY)

When an override is applied, the audit must record:

* A top-level or rationale-level marker indicating overrides were applied, for example:

  * add `human_override_applied` to `rationale.flags` (or equivalent)

* A structured list of applied overrides, for example under:

  * `audit["human_overrides_applied"] = [...]`

Each applied override record must include:

```json
{
  "gsm_accession": "GSM67890",
  "field": "disease",
  "old_value": "No",
  "new_value": "Hepatocellular carcinoma",
  "reason": "Curator confirmed in GEO record",
  "curator": "tl",
  "timestamp": "2026-01-07T10:30:00Z"
}
```

Rules:

* `old_value` must be captured from the pre-override final output
* Optional fields (`reason`, `curator`, `timestamp`) are included if present in input
* If an override matches the existing value, it should either:

  * be omitted from `human_overrides_applied`, or
  * be recorded with a flag like `"no_op": true`
    Choose one approach and keep it consistent and deterministic

---

### Output Requirements

Overrides must affect:

* `audit.jsonl` final output fields
* `curation.tsv` (via `_build_curation_row` final_output)
* `curation.jsonl` (lossless mirror of TSV)
* Any other “final output” artifacts that represent the final chosen labels

This ticket must not modify:

* evidence emission logic (Ticket-35) beyond reflecting updated final outputs if evidence refers to outputs

---

### CLI / Config Changes

Add an optional CLI argument (or config entry) to specify overrides:

* `--overrides path/to/overrides.jsonl`

Behavior:

* If provided:

  * load overrides at run start
  * validate
  * apply at write time
* If not provided:

  * do nothing

Error behavior:

* Invalid overrides file must terminate the run with clear validation errors

---

### Determinism Requirements

* Overrides must be applied in a deterministic order:

  * sort by `(gsm_accession, field)` before application (or use a deterministic structure from loader)
* For identical inputs + identical overrides file:

  * outputs and audits must be byte-identical across runs

---

### Acceptance Criteria

**Functional**

* Overrides file can be provided via CLI
* Overrides are applied to final outputs for targeted GSM/fields
* No extra LLM calls are triggered

**Correctness**

* Without overrides: outputs are byte-identical to baseline
* With overrides: only the specified GSM/fields change
* Audit records include:

  * `human_override_applied` flag
  * full list of applied override records with old/new values

**Compatibility**

* Existing workflows continue to work without modification
* Curation TSV/JSONL remain valid and consistent

---

### Tests Required

1. **No-overrides regression**

   * Run with no overrides file
   * Assert outputs identical to baseline (golden)

2. **Single override**

   * Override one field on one GSM
   * Assert only that field changes in:

     * final output
     * curation.tsv
     * curation.jsonl
   * Assert audit contains correct applied override record

3. **Multiple overrides**

   * Override multiple fields and multiple GSMs
   * Assert deterministic order and correctness

4. **No-op override**

   * Override sets a field to the same value
   * Assert behavior matches the chosen policy (omit or record with no_op)

5. **LLM call guard**

   * Instrument or mock LLM client
   * Assert no additional calls are made due to overrides

---

### Non-Goals (Explicit)

* No UI
* No ontology validation of override values
* No re-repair or re-grounding after override
* No persistence beyond file input

---

### Documentation Updates

* Update `docs/RESUME.md`:

  * Mention `--overrides` support and deterministic application
* Update latest checkpoint document:

  * Summarize override application behavior and audit provenance

---

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-36.md` and paste this ticket verbatim.

---

### Codex working-note (MANDATORY)

At the start of the Codex session:

> **Working on ticket-36**

This note must remain visible in:

* Codex session notes
* Commit messages related to this ticket
