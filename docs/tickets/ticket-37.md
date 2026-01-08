# Ticket #37: CURATION-005 — Emit cross-GSM suggestions (opt-in, non-forcing)

## Background

v0.4 allows curators to review GSMs individually. However, many issues are only visible **in aggregate**, for example:

* a single GSM disagrees with the majority of a GSE
* inconsistent disease or organism labels across GSMs
* rare outliers that deserve manual inspection

This ticket introduces a **cross-GSM suggestion engine** that analyzes existing final outputs and emits **suggestions only**, never modifying GSM labels.

Suggestions are advisory, optional, and explicitly separated from final outputs.

---

## Scope (STRICT)

**In scope**

* Analyze GSM-level final outputs within a GSE or run
* Emit suggestions as a separate artifact (`suggestions.jsonl`)
* Deterministic, rule-based aggregation only
* Opt-in via CLI/config flag

**Out of scope**

* Automatically changing any GSM outputs
* Writing overrides automatically
* LLM calls or inference
* UI implementation
* Cross-run persistence

---

## Goals

1. Help curators **spot inconsistencies and outliers**
2. Preserve GSM independence and determinism
3. Keep suggestions clearly advisory and ignorable
4. Enable future UI surfacing without coupling logic

---

## Activation (Opt-in Only)

Suggestions must be emitted **only if explicitly requested**:

* CLI flag:

  ```
  --emit-suggestions
  ```

If the flag is not present:

* No aggregation
* No `suggestions.jsonl` emitted
* Zero behavior change

---

## Source of Truth (MUST)

Suggestions must be computed **only from existing artifacts**, such as:

* `curation.jsonl` (preferred)
* or equivalent in-memory final outputs

Prohibited:

* LLM calls
* Reading raw GSM text
* Ontology expansion or synonym reasoning
* Using overrides to bias suggestions

Overrides may be *reported* but must not change suggestion logic.

---

## Canonical `suggestions.jsonl` Record Structure (v1)

One JSON object per suggestion.

```json
{
  "scope": "GSE",
  "gse_accession": "GSE12345",
  "gsm_accession": "GSM67890",
  "field": "disease",
  "current_value": "No",
  "suggested_value": "Hepatocellular carcinoma",
  "support_fraction": 0.92,
  "support_count": 23,
  "total_count": 25,
  "reason": "value_outlier_within_gse"
}
```

---

## Field Semantics

* `scope`

  * Fixed value: `"GSE"` (future-proofing)

* `gse_accession`

  * Required

* `gsm_accession`

  * Required (suggestions are GSM-specific)

* `field`

  * One of canonical output fields:

    * `data_type`, `organism`, `tissue_type`, `cell_line`, `disease`, `treatment`

* `current_value`

  * Final output value for this GSM

* `suggested_value`

  * Majority or dominant value within the aggregation scope

* `support_fraction`

  * `support_count / total_count`
  * Float, deterministic rounding (document precision)

* `support_count`

  * Number of GSMs supporting `suggested_value`

* `total_count`

  * Total GSMs considered for this field

* `reason`

  * One of:

    * `value_outlier_within_gse`
    * `rare_value_within_gse`
    * `singletons_within_gse`

No other reasons in this ticket.

---

## Suggestion Rules (Deterministic)

At minimum, implement:

1. **Majority outlier rule**

   * If ≥ X% (recommend X = 0.8) of GSMs share the same value
   * And a GSM differs
   * Emit a suggestion for that GSM

2. **Singleton rule**

   * If a value appears exactly once in a GSE
   * Emit a suggestion flagging it as singleton

Rules must:

* Be parameterized with constants
* Be deterministic
* Be documented in code

---

## Ordering and Determinism

* Suggestions must be emitted in deterministic order:

  * Sort by `(gse_accession, field, gsm_accession)`
* Floating values must be rounded deterministically (for example 3 decimals)

---

## Output Location and Naming

* Emit `suggestions.jsonl` in the same output directory as:

  * `curation.tsv`
  * `curation.jsonl`
  * `evidence.jsonl`

---

## Acceptance Criteria

**Functional**

* `suggestions.jsonl` is emitted only when `--emit-suggestions` is provided
* One suggestion per GSM/field that meets rules

**Correctness**

* Suggestions are consistent with aggregate statistics
* No GSM output values are changed

**Safety**

* No LLM calls
* No hidden state or persistence

---

## Tests Required

1. **No-flag test**

   * Run without `--emit-suggestions`
   * Assert `suggestions.jsonl` does not exist

2. **Majority rule test**

   * Synthetic GSE where 9/10 GSMs share a value
   * Assert suggestion emitted for the outlier

3. **Singleton test**

   * One-off value
   * Assert singleton suggestion emitted

4. **Determinism test**

   * Same inputs → identical `suggestions.jsonl`

---

## Non-Goals (Explicit)

* No override generation
* No UI hints or rendering
* No ontology synonym logic
* No cross-GSE aggregation

---

## Documentation Updates

* Update `docs/RESUME.md`:

  * Describe `suggestions.jsonl` as advisory-only
* Update latest checkpoint:

  * Note opt-in cross-GSM suggestions

---

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-37.md` and paste this ticket verbatim.

---
