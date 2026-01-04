Ticket #17-c: AGENT-WS-017c — Clean raw field values before ontology scoring (strip “key: value” prefixes) + regression tests

You are working in repo `geo-gsm-annotator-agent`.

## Context

Ontology grounding now successfully queries the existing ChromaDB, but many records are still flagged with `ontology_low_confidence_*`.

A confirmed repro case (positive control):

* `raw_value` for `tissue_type` becomes `"tissue: liver"`
* Retriever returns correct candidates including `UBERON:0002107 (liver)`
* Deterministic scorer uses token Jaccard; `"tissue liver"` vs `"liver"` yields 0.5
* Threshold rejects as LOW_CONFIDENCE, even though it should be MATCHED.

Root cause: **raw field values often contain prefix noise like `tissue: ...`, `disease: ...`, `cell line: ...`** which must be cleaned before normalization/tokenization.

## Goal

Implement deterministic preprocessing of raw field values (for ontology-grounded fields) so that prefix patterns like `"<key>: <value>"` are stripped prior to scoring. Add regression tests proving the fix.

## Non-goals

* Do not change Chroma retrieval logic.
* Do not change the 8-field output schema.
* Do not change the overall decision engine; only reduce false LOW_CONFIDENCE outcomes.

---

## A) Implement a shared raw-value cleaner

### New function

Add a helper in a shared module (choose one):

* `src/validator/ontology_match.py` (preferred if small), or
* `src/validator/ontology_match_utils.py` (if you want to keep ontology_match clean)

Function signature:

```python
def clean_raw_value_for_ontology(raw_value: str) -> str:
    ...
```

### Requirements

1. Trim whitespace.
2. Strip common “key: value” prefixes deterministically.

Minimum rule (must implement):

* If the full string matches:

  * `^[A-Za-z][A-Za-z0-9 _/\-]{0,40}:\s*(.+)$`
  * replace with group(1)

Example:

* `"tissue: liver"` -> `"liver"`
* `"disease: HIV-1"` -> `"HIV-1"`
* `"cell line: K562"` -> `"K562"`

3. Do not be overly aggressive:

* Only strip a single leading `something:` prefix.
* Limit the “key” length (<= 40 chars) to avoid stripping real content.

Optional improvements (nice-to-have, but keep deterministic):

* Also strip `key = value` and `key - value` if present:

  * `^\s*<key>\s*=\s*(.+)$`
  * `^\s*<key>\s*-\s*(.+)$`

---

## B) Apply cleaning in ontology selection

Update the deterministic selection function (likely `choose_best_ontology_candidate` in `src/validator/ontology_match.py`) to:

1. Preserve original raw_value for audit.
2. Use `clean_raw_value_for_ontology(raw_value)` for:

   * normalization
   * tokenization
   * label/synonym exact match
   * token overlap scoring

This should convert the repro score from 0.5 to 1.0 in the example.

---

## C) Ensure cleaning is applied for all ontology-grounded fields

Confirm that `choose_best_ontology_candidate` is called by all relevant grounders:

* `src/validator/grounders/tissue_type.py`
* `src/validator/grounders/disease.py`
* `src/validator/grounders/cell_line.py`
* `src/validator/grounders/data_type.py`

No per-field hacks. One shared cleaner.

---

## D) Tests (required)

Add a new test file:

* `tests/test_ontology_clean_raw_value.py`

### Unit tests for cleaner

* `"tissue: liver"` -> `"liver"`
* `"disease: HIV-1"` -> `"HIV-1"`
* `"cell line: K562"` -> `"K562"`
* `"liver"` -> `"liver"` (no change)
* `"tissue:liver"` -> `"liver"` (no space)
* `"tissue:  liver "` -> `"liver"` (extra spaces)

### Regression test for selection logic (no Chroma required)

Mock candidates (as your selection function consumes) and assert:

Input:

* raw_value = `"tissue: liver"`
  Candidates:
* `label="liver", term_id="UBERON:0002107"`
* `label="tissue", term_id="UBERON:0000479"`

Expected:

* status == MATCHED
* best.term_id == `"UBERON:0002107"`
* confidence == 1.0 (or >= configured accept threshold)

This test should fail before the fix and pass after.

---

## E) Acceptance criteria

* Running the earlier positive-control JSONL yields:

  * `tissue_type.status == MATCHED`
  * `matched_term_id == UBERON:0002107`
* `pytest -q` passes.
* No change to output schema.

---

## Implementation notes

* Keep the cleaner deterministic and conservative.
* Do not change thresholds as part of this ticket. The point is to remove avoidable prefix noise so correct exact matches can be accepted.

---
