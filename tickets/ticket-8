Ticket #8: AGENT-WS-008 Implement bounded repair loop controller (decision engine + state updates)

You are working in repo `geo-gsm-annotator-agent` (src-layout under `src/`).

Goal:
Implement the repair loop that:
- takes validation failures
- asks the decision engine what to do
- updates PipelineState deterministically
- enforces per-field repair limits
This ticket does NOT call a real LLM. Repair execution is stubbed.

Files to implement/update:
- `src/agent/repair_loop.py` (currently placeholder)
- Add tests: `tests/test_repair_loop.py`

Inputs:
- PipelineState (from agent/state.py)
- decision engine:
  - `decide_next_action(...)`
- decision table loaded elsewhere and passed in

Public API:
Implement in `agent/repair_loop.py`:

```python
def apply_repairs(
    state: PipelineState,
    decision_table: dict,
    max_total_repairs: int | None = None,
) -> PipelineState:
    ...
````

Core logic:

1. If state has no failures (format, semantic, ontology, consistency):

   * set `state.final_decision = "ACCEPT"`
   * return state

2. While repairs are allowed:

   * Call decision engine:

     * inputs:

       * failures_by_field (merge semantic + ontology failures)
       * attempts_by_field
   * Get a Decision object

3. Decision handling:

   * ACCEPT:

     * set final_decision="ACCEPT"
     * return state
   * FALLBACK:

     * write fallback_value into `state.final_output[field]`
     * increment attempts_by_field[field]
     * record repair_history entry
     * remove that field’s failures
     * continue loop
   * REPAIR:

     * increment attempts_by_field[field]
     * append to repair_history:
       {failure_code, field, repair_template}
     * STUB the repair result:

       * Do NOT call LLM
       * Simply leave llm_parsed_outputs unchanged
       * Keep failures unless fallback clears them
     * continue loop
   * ESCALATE:

     * set final_decision="FLAGGED"
     * add failure_code to state.flags
     * return state

4. Stopping conditions:

   * Per-field attempts must not exceed decision_table max_attempts
   * If max_total_repairs is set and exceeded:

     * set final_decision="FLAGGED"
     * add flag "max_repairs_exceeded"
     * return state

5. At loop end:

   * If failures remain unresolved:

     * final_decision="FLAGGED"
   * Else:

     * final_decision="ACCEPT"

State mutation rules:

* DO NOT erase historical data
* DO NOT reset attempts
* repair_history must be append-only
* attempts_by_field increments only when a decision targets that field

Unit tests (pytest):
Create `tests/test_repair_loop.py` with tests:

Test cases:

1. No failures -> ACCEPT
2. tissue_is_cell_type -> REPAIR twice -> FALLBACK Unknown -> ACCEPT
3. disease_unsupported -> immediate FALLBACK Healthy -> ACCEPT
4. unknown failure -> ESCALATE -> FLAGGED
5. max_total_repairs enforced -> FLAGGED

For tests:

* Manually construct PipelineState with:

  * semantic_errors and/or ontology_failures populated
  * empty llm outputs (this is fine)
* Load decision_table from `spec/decision_table.yaml`

Constraints:

* Deterministic behavior
* No LLM calls
* No parser calls
* No Chroma calls
* Use only stdlib + pytest

After implementation:

* run `uv run python -m pytest -q`

Deliverables:

* `src/agent/repair_loop.py`
* `tests/test_repair_loop.py`

