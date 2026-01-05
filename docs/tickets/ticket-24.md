# Ticket #24: AGENT-WS-024 — Wire repair loop into CLI pipeline (all run modes)

## Background

The repair loop (`agent.repair_loop.apply_repairs`) is fully implemented and tested in isolation, but it is **never invoked** in the current pipeline. A repository-wide search confirms there are **no call sites** for `apply_repairs()`.

As a result:

* Decision table rules (REPAIR / FALLBACK / ESCALATE) are never executed.
* Semantic failures such as `cell_line_is_cell_type` and `disease_inferred_without_evidence` cannot trigger fallback or repair.
* Audit records show ontology fallback status, but `final_output` remains unchanged.
* Flags and repair history are misleading, since no actual repair loop runs.

This is a **wiring bug**, not a logic bug.

---

## Goal

Ensure the repair loop is executed **after validation** and **before final output is written**, for all CLI execution paths:

* `--gsm`
* `--gsm-file`
* `--jsonl`
* `--gse`

---

## Scope

### In scope

* Integrate `apply_repairs()` into the main pipeline
* Ensure semantic, ontology, and consistency failures are visible to the decision engine
* Ensure FALLBACK decisions update `state.final_output`
* Preserve existing validation and audit behavior

### Out of scope

* Changing repair policies
* Adding new failure codes
* Changing thresholds or ontology logic

---

## Required changes

### 1. Identify pipeline entry points

Locate the functions responsible for end-to-end execution, likely in:

* `src/agent/run_single.py`
* `src/agent/run_batch.py`
* `src/agent/run_gse.py`

Each path should have a structure like:

1. Construct prompt
2. LLM generation
3. Parse output → `state.final_output`
4. Validation (format / semantic / ontology / consistency)
5. **Repair loop (missing today)**
6. Final decision + write outputs

---

### 2. Wire in the repair loop

Insert a call to `apply_repairs()` **after validation populates failures**:

```python
from agent.repair_loop import apply_repairs

state = apply_repairs(
    state=state,
    decision_table=decision_table,
    llm_client=llm_client,
    context_text=context_text,
    prompt_loader=prompt_loader,
    max_total_repairs=config.max_total_repairs,
)
```

Notes:

* `context_text` must be the same text used for the original prompt
* `prompt_loader` must resolve repair templates
* `decision_table` should already be loaded (from `decision_table.yaml`)
* `max_total_repairs` should come from config if present, else None

---

### 3. Ensure failures are visible to the repair loop

Confirm that before calling `apply_repairs()`:

* `state.semantic_errors`
* `state.ontology_failures`
* `state.consistency_flags`

are already populated.

Do **not** recompute validation after the repair loop unless explicitly intended.

---

### 4. Update final output handling

After `apply_repairs()` returns:

* Use `state.final_output` as the authoritative output
* Use `state.final_decision` to determine ACCEPT vs FLAGGED
* Do not overwrite repaired fields with pre-repair values

---

## Acceptance criteria

### Functional

* `apply_repairs()` is called for all CLI modes
* FALLBACK rules modify `final_output`

  * Example: `cell_line_is_cell_type` → `"No"`
  * Example: `disease_inferred_without_evidence` → `"Healthy"` or `"Unknown"` (per policy)
* REPAIR rules trigger LLM repair prompts
* ESCALATE results in `final_decision = FLAGGED`

### Audit

* `repair_history` reflects actual repair/fallback actions
* `attempts_by_field` increments correctly
* Flags are consistent with final decision

### Tests

* Add at least one unit test asserting:

  * semantic error → FALLBACK → final_output updated
* Existing tests continue to pass (`uv run pytest -q`)

---

## Suggested implementation order

1. Wire repair loop into `run_single`
2. Mirror wiring in `run_batch` and `run_gse`
3. Add a minimal unit test for fallback application
4. Run full test suite

---

## Notes

This ticket is **blocking** for all repair-related policies implemented so far (tickets 18–23). Without this wiring, repair logic exists only on paper.

---
