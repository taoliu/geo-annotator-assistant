# Ticket #35: CURATION-003 — Emit structural evidence diagnostics (`evidence.jsonl`)

### Background

v0.4 introduces curator-facing workflows that require transparency into *why* a GSM annotation is strong, weak, or fragile.

Current audits already contain **deterministic structural signals** that explain decision quality, such as:

* repair attempts per field
* terminal fallback usage
* ontology grounding status
* GSE-level outlier flags

This ticket surfaces those existing signals in a **machine-readable, UI-friendly artifact** called `evidence.jsonl`.

This ticket is **purely extractive**.
No new inference, no text generation, and no decision changes are allowed.

---

### Scope (STRICT)

**In scope**

* Emit `evidence.jsonl`, one record per GSM
* Structural evidence derived only from existing audit data
* Field-scoped diagnostics
* Deterministic output

**Out of scope**

* Free-text evidence or rationale
* New LLM calls
* Re-parsing GSM text
* Applying overrides
* UI implementation
* Cross-GSM aggregation

---

### Goals

1. Expose **why a field may be unreliable or stable**
2. Support curator review without changing behavior
3. Preserve determinism and audit guarantees
4. Provide a clean foundation for future textual evidence (v0.5+)

---

### Definition of “Evidence” (v0.4)

Evidence means **structural diagnostics already present in audits**, including:

* number of repair attempts
* terminal fallback usage
* ontology grounding status
* relevant flags

No natural-language explanations are included in this version.

---

### Canonical `evidence.jsonl` Record Structure (v1)

One JSON object per GSM.

```json
{
  "gse_accession": "GSE12345",
  "gsm_accession": "GSM67890",
  "evidence_by_field": {
    "data_type": {
      "attempts": 1,
      "terminal_fallback": false,
      "ontology_status": "",
      "flags": []
    },
    "organism": {
      "attempts": 1,
      "terminal_fallback": false,
      "ontology_status": "grounded",
      "flags": []
    },
    "tissue_type": {
      "attempts": 2,
      "terminal_fallback": false,
      "ontology_status": "grounded",
      "flags": []
    },
    "cell_line": {
      "attempts": 0,
      "terminal_fallback": false,
      "ontology_status": "",
      "flags": []
    },
    "disease": {
      "attempts": 3,
      "terminal_fallback": true,
      "ontology_status": "synonym",
      "flags": ["gse_outlier_disease"]
    },
    "treatment": {
      "attempts": 0,
      "terminal_fallback": false,
      "ontology_status": "",
      "flags": []
    }
  }
}
```

---

### Field Semantics

#### Top-level keys

* `gse_accession`
* `gsm_accession`
* `evidence_by_field`

#### `evidence_by_field`

* Keys:

  * Must be limited to the **canonical output fields**:

    * `data_type`
    * `organism`
    * `tissue_type`
    * `cell_line`
    * `disease`
    * `treatment`
* Values:

  * An object with the following keys:

| Key                 | Type   | Source                                  |
| ------------------- | ------ | --------------------------------------- |
| `attempts`          | int    | `rationale["attempts_by_field"]`        |
| `terminal_fallback` | bool   | `rationale["terminal_fallback_fields"]` |
| `ontology_status`   | string | `rationale["ontology_status_by_field"]` |
| `flags`             | list   | GSM-level flags relevant to the field   |

Missing data must be represented with defaults:

* `attempts`: `0`
* `terminal_fallback`: `false`
* `ontology_status`: `""`
* `flags`: `[]`

---

### Source of Truth Requirement (MUST)

All evidence must be derived **only** from existing audit structures, including:

* `audit["rationale"]`
* `audit["flags"]`
* `audit` keys prefixed with `gse_outlier_`

Prohibited:

* LLM calls
* GSM text parsing
* Generating or summarizing text
* Guessing confidence

---

### Implementation Guidance (Non-prescriptive)

* Implement a builder:

  ```
  build_evidence_record(annotation, audit) -> Dict
  ```
* Field iteration order must follow the canonical field list
* Evidence extraction must be defensive against missing keys

---

### Output Location and Naming

* Emit `evidence.jsonl` in the same output directory as:

  * `curation.tsv`
  * `curation.jsonl`
* File name must be exactly: `evidence.jsonl`

---

### Determinism Requirements

* For identical inputs and config:

  * `evidence.jsonl` must be byte-identical across runs
* Ordering:

  * GSM records must follow run order
  * Field order must be canonical and stable

---

### Acceptance Criteria

**Functional**

* `evidence.jsonl` is produced for GSM-level runs
* One JSON object per GSM

**Correctness**

* All values match existing audit data exactly
* No missing required keys
* No free-text evidence present

**Safety**

* No LLM calls during emission
* No crashes if rationale fields are missing

---

### Tests Required

1. **Presence test**

   * Ensure `evidence.jsonl` is created

2. **Schema test**

   * Assert required keys exist
   * Assert correct defaults for missing data

3. **Audit consistency test**

   * Cross-check values against `audit.jsonl`

4. **Determinism test**

   * Two identical runs produce identical `evidence.jsonl`

---

### Non-Goals (Explicit)

* No textual explanations
* No scoring or ranking
* No override application
* No UI rendering

---

### Documentation Updates

* Update `docs/RESUME.md`:

  * Describe `evidence.jsonl` as a structural diagnostic artifact
* No whitepaper update required

---

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-35.md` and paste this ticket verbatim.

---

### Codex working-note (MANDATORY)

At the start of the Codex session:

> **Working on ticket-35**

This note must remain visible in:

* Codex session notes
* Commit messages related to this ticket

---
