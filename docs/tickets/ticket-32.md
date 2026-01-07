# Ticket #32: PERF-001 — Reuse local HF LLM across GSMs (single GPU, single process)

## Background

Current runs load the local HuggingFace LLM repeatedly when processing multiple GSMs.
On a single-GPU setup, this causes unnecessary model initialization overhead and becomes the dominant runtime cost for GSE-scale processing.

This ticket introduces **process-level model reuse** so that:

* The model is loaded **once per run**
* The same model instance is reused for all GSMs
* No behavior, outputs, or decision logic changes

This is a **performance-only ticket**. No UI, no schema changes, no architectural redesign.

---

## Scope (STRICT)

**In scope**

* Single process
* Single GPU
* Local HuggingFace Transformers backend
* Deterministic reuse of one model instance across GSMs in the same run
* Lightweight benchmarking and logging

**Out of scope**

* Multi-GPU
* Multiprocessing / distributed execution
* vLLM / TGI / remote inference
* UI changes
* Any change to decision logic, repair loop, or ontology grounding

---

## Problem Statement

Model initialization (for example `AutoModel.from_pretrained`, `pipeline(...)`) is currently triggered at GSM-level granularity instead of run-level granularity.

This leads to:

* Repeated GPU memory allocation
* Repeated model weight loading
* Significant slowdown for large GSM batches

---

## Design Requirements

1. **Model lifecycle**

   * The LLM must be initialized **once per pipeline run**
   * All GSMs must reuse the same model object
   * No implicit reloads during GSM iteration

2. **Determinism**

   * For identical inputs and fixed seeds, outputs must remain identical to pre-change behavior
   * No additional randomness introduced

3. **Isolation**

   * Model reuse must be local to the process
   * No global state leakage across independent runs

4. **Transparency**

   * Log clearly when the model is initialized
   * Log must show exactly one initialization per run

---

## Proposed Implementation (Guidance)

This is **guidance**, not a prescription.

* Introduce a cached LLM factory or singleton, keyed by:

  ```
  (model_id, revision, device, dtype, quantization)
  ```
* Instantiate the model:

  * At pipeline startup
  * Or via lazy initialization on first use
* Pass the model client down to GSM-level functions **without re-instantiation**

Acceptable patterns:

* Module-level cache with explicit getter
* PipelineState-attached `llm_client`
* Explicit `LLMClient` object passed through call stack

Avoid:

* Instantiating pipelines/models inside GSM loops
* Hidden reloads triggered by helper functions

---

## CLI / Config Changes

None required.

Optional (if trivial):

* `--benchmark` flag (see below)

---

## Logging and Benchmarking

Add minimal, explicit logs:

* On model load:

  ```
  [LLM] Initializing model: <model_id> on <device>
  ```
* On reuse:

  ```
  [LLM] Reusing existing model instance
  ```

Optional but recommended:

* `--benchmark` flag that prints:

  * model init time
  * total runtime
  * number of GSMs processed
  * GSMs per second

Benchmark output must be informational only and not affect outputs.

---

## Acceptance Criteria

**Functional**

* Model is loaded exactly once per run (verified via logs)
* All GSMs reuse the same model instance
* No crashes, no GPU memory leaks

**Correctness**

* For a fixed input set and seed:

  * Output files are byte-identical before vs after this change
* Decision paths, repair behavior, and ontology grounding remain unchanged

**Performance**

* For a multi-GSM run:

  * Model initialization time occurs once
  * Total runtime scales approximately linearly with GSM count after init

---

## Tests Required

1. **Unit / structural**

   * Verify model factory returns the same object for repeated calls
   * Or mock and assert initialization called once

2. **Integration**

   * Run a small batch (for example 2–3 GSMs)
   * Assert exactly one model initialization log line

3. **Regression**

   * Compare outputs before vs after for the same inputs
   * Outputs must match exactly

---

## Risks and Mitigations

* **Risk**: Hidden code path still instantiates model
  **Mitigation**: Centralize all model creation behind one factory

* **Risk**: GPU OOM due to lingering references
  **Mitigation**: Ensure only one model instance exists; no per-GSM pipelines

---

## Non-Goals (Explicit)

* No attempt to parallelize GSMs
* No batching changes
* No inference optimization beyond reuse
* No UI integration

---

## Documentation Updates

* Update `docs/checkpoints/2026-01-06_checkpoint.md` with:

  * Description of model reuse
  * Measured speed improvement (qualitative or quantitative)

No whitepaper update required for this ticket.

---

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-32.md` and paste this ticket verbatim.

---

## Codex working-note (MANDATORY)

At the start of the Codex session:

> **Working on ticket-32**

This note must remain visible in:

* Codex session notes
* Commit messages related to this ticket
