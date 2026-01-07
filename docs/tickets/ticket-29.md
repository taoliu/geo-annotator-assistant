## Ticket #29: GSE-level consistency report and outlier flags (no label propagation)

### Problem

When running `agent.cli --gse`, GSM-level outputs can vary across samples within the same GSE, especially for `tissue_type` and `disease`. Some variation is real (old GEO, mixed assays/organisms), so we must **not** propagate labels from one sample to another.

We still need a structured way to:

* quantify within-GSE inconsistency
* identify outlier GSMs per field
* surface this in audit logs for review and downstream filtering

### Goal

Add a **post-pass** to GSE runs that produces:

1. A **GSE-level consistency report** summarizing value distributions per field.
2. Per-GSM **outlier flags** in audit records (non-blocking), without changing any labels.

### Scope

**In scope**

* Implement GSE post-pass logic in the `--gse` / `run_gse_from_jsonl` path
* Generate a `gse_consistency.json` report in the output directory
* Add `gse_outlier_<field>` flags to audit records when applicable
* Add unit tests for report structure and outlier detection

**Out of scope**

* Auto-correcting or propagating labels across GSMs
* Changes to ontology/semantic validators
* Changing accept/flag decisions based on outliers (for now)

### Fields to include

Compute distributions for:

* `data_type`
* `organism`
* `tissue_type`
* `cell_line`
* `disease`

### Placeholder filtering (configurable)

When computing distributions and “dominant value”:

* ignore placeholders:

  * `Unknown`
  * `None`
  * `No`
  * `Healthy`

Make this configurable via config, defaulting to the above list.

Suggested config block:

```yaml
postpass:
  gse_consistency:
    enabled: true
    fields: ["data_type","organism","tissue_type","cell_line","disease"]
    ignore_values: ["Unknown","None","No","Healthy"]
    outlier_min_samples: 5
    outlier_min_dominant_fraction: 0.80
```

### Outlier definition

For each field:

* Consider only non-placeholder values.
* If the number of non-placeholder samples `< outlier_min_samples`, do not label outliers for that field.
* Let `dominant_value` be the most frequent value and `dominant_fraction = count(dominant_value)/N`.
* If `dominant_fraction >= outlier_min_dominant_fraction`, then any GSM with a different non-placeholder value is an outlier:

  * add audit flag: `gse_outlier_<field>`

This avoids false outliers when a GSE is genuinely mixed.

### Output report

Write a JSON file in the run output dir:

* `gse_consistency.json`

Suggested structure:

```json
{
  "gse_accession": "GSE229352",
  "n_total": 12,
  "ignore_values": ["Unknown","None","No","Healthy"],
  "fields": {
    "tissue_type": {
      "n_non_placeholder": 10,
      "dominant_value": "Breast",
      "dominant_fraction": 0.9,
      "counts": {"Breast": 9, "Primary mouse mammary fibroblasts": 1},
      "outliers": ["GSM..."]
    },
    ...
  }
}
```

### Where to implement

* In `agent/run_gse.py` (or wherever GSE results are gathered), after annotations/audits are collected and before writing outputs.
* Ensure the report is written by `writer.py` (extend `write_run_outputs()` to include this optional artifact), or write it in the CLI after `write_run_outputs()` returns.

Preferred: extend `write_run_outputs()` to optionally accept `extra_files` or a `report` dict.

### Acceptance Criteria

* Running `agent.cli --gse <GSE>` produces `gse_consistency.json` under the output dir.
* Audit records include `gse_outlier_<field>` flags when the outlier rule triggers.
* No labels are modified during post-pass.
* Existing tests pass.
* New tests cover:

  * distribution computation
  * dominant fraction thresholding
  * outlier flagging behavior
  * placeholder exclusion behavior
