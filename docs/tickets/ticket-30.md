# Ticket #30: Deterministic accession override to prevent LLM identity leakage (gse_accession/gsm_accession)

### Problem

In real-world runs, the LLM frequently corrupts accession identifiers inside otherwise valid JSON outputs, for example:

* `gse_accession`: `GSE292952`, `GSE29-2352`, `GSE2-9-2352` (should be `GSE229352`)
* `gsm_accession`: `GSM1791882`, `GSM1-7-9182` (should be the true GSM)

This is not a semantic labeling problem. These identifiers are already known by the pipeline and should be treated as authoritative. Identity leakage creates:

* noisy audits
* unnecessary repair attempts
* confusion when tracing outputs

### Goal

Ensure `gse_accession` and `gsm_accession` are always set deterministically from pipeline context, regardless of what the LLM outputs.

### Scope

**In scope**

* Override `gse_accession`/`gsm_accession` after any LLM parse step (initial output, format repairs, decision repairs)
* Ensure audits/annotations always reflect the authoritative accessions

**Out of scope**

* Changing prompts
* Changing validators/ontology logic
* Cross-sample propagation

### Design

Introduce a small helper, used in the pipeline wherever parsed JSON is accepted:

**Helper behavior**

* Given a parsed dict and authoritative values `(true_gse, true_gsm)`:

  * set `parsed["gse_accession"] = true_gse` if `true_gse` is non-empty
  * set `parsed["gsm_accession"] = true_gsm` always
* Apply this after each successful `validate_format()` parse

### Implementation Locations

1. `agent/run_single.py`

   * In `_generate_with_format_repairs()`:

     * after `validate_format()` returns a non-None `parsed_output`, override IDs before appending to `state.llm_parsed_outputs` and before returning.
   * In decision repair path (`apply_repairs` / REPAIR path or the caller):

     * after `validate_format()` returns parsed output, override IDs before updating `state.final_output`.

2. If REPAIR parsing happens inside `agent/repair_loop.py`:

   * Apply the same override there (preferred, since REPAIR runs in that file).

3. Ensure `run_single_from_context_record()` uses `record["gse_accession"]` + `record["gsm_accession"]` as authoritative sources.

4. Ensure `run_single_gsm()` uses `state.gse_accession` (from parser) + `state.gsm_accession`.

### Acceptance Criteria

* For a GSE run where the LLM produces malformed accessions, final outputs still contain the correct accessions.
* Audit `llm_parsed_outputs` may still record the model’s raw parsed value (optional), but:

  * `final_output.gse_accession` and `final_output.gsm_accession` must always be correct
  * the annotation output must always be correct
* No regressions in existing unit tests.
* Add at least one unit test that simulates an LLM output with wrong accessions and asserts final output uses authoritative IDs.

### Suggested Test

* Stub a parsed output (or stub LLM response) that returns:

  * `{"gse_accession":"GSE2-9-2352","gsm_accession":"GSM1-7-9182", ...}`
* Run through `run_single_from_context_record()` and assert:

  * final output IDs equal the record IDs

---
