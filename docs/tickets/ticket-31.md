# Ticket #31: Add curator-ready rationale block and TSV export

## Problem

`audit.jsonl` is machine-complete but human-expensive.
Curators need a **single-glance explanation** of:

* why a GSM was ACCEPT / FLAGGED
* which fields failed or were terminal-fallbacked
* how much LLM effort was spent
* whether GSE-level inconsistency was involved

A future UI will need structured signals, not free-text logs.

## Goal

Augment outputs with **curation-ready summaries** without changing pipeline behavior.

## Scope

**In scope**

1. Add a compact `rationale` block to each audit record
2. Emit a curator-friendly TSV file (one row per GSM)
3. Reuse existing state; no new inference or validation

**revealed-but-not-used**

* GSE outlier flags from Ticket #29
* terminal fallback tracking from Ticket #28

**Out of scope**

* UI / dashboard
* manual override workflows
* policy changes

---

## 1. `rationale` block in audit.jsonl

Add a top-level object to `build_audit_record()`:

```json
"rationale": {
  "final_decision": "ACCEPT",
  "primary_failure": "tissue_type_is_cell_type",
  "terminal_fallback_fields": ["tissue_type", "disease"],
  "n_llm_calls": 4,
  "attempts_by_field": {"tissue_type": 2, "disease": 3},
  "ontology_status_by_field": {
    "data_type": "MATCHED",
    "tissue_type": "FALLBACK",
    "disease": "FALLBACK",
    "cell_line": "FALLBACK"
  },
  "flags": ["gse_outlier_tissue_type"]
}
```

**Notes**

* `primary_failure` = first decisive failure that triggered repair/escalation
* `ontology_status_by_field` pulled from `ontology_matches`
* `n_llm_calls = len(llm_raw_outputs)`
* No free text, all structured

---

## 2. Curator TSV export

Add a new output file:

```
curation.tsv
```

One row per GSM. Suggested columns:

```
gse_accession
gsm_accession
final_decision
data_type
organism
tissue_type
cell_line
disease
treatment
primary_failure
terminal_fallback_fields
n_llm_calls
attempts_by_field
ontology_status_tissue_type
ontology_status_disease
flags
```

* TSV, UTF-8
* Safe to open in Excel / LibreOffice
* This becomes the **human entry point** for review

Implementation location:

* Extend `writer.py`
* Either:

  * add `write_curation_tsv()`, or
  * extend `write_run_outputs()` to optionally emit TSV

---

## Acceptance Criteria

* All existing tests pass
* `audit.jsonl` includes `rationale` block
* `curation.tsv` is written for batch / GSE runs
* No change in ACCEPT/FLAGGED outcomes
* No additional LLM calls

---

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-31.md` and paste this ticket verbatim.

---
