Ticket #14: AGENT-WS-014 — Route consistency flags via decision table (no direct auto-flag) + regression tests

You are working in repo `geo-gsm-annotator-agent`.

Ticket: AGENT-WS-014 — Route consistency flags via decision table (no direct auto-flag) + regression tests

Problem observed:
Running `agent.cli --jsonl GSE112494.jsonl` flags all samples due to the consistency flag `healthy_disease_conflict`.
Audit shows:
- format_errors empty
- semantic_errors empty
- ontology_failures empty
- consistency_flags contains healthy_disease_conflict
- flags contains healthy_disease_conflict
- final_decision FLAGGED
This is too strict and blocks stub-mode end-to-end runs.

Goal:
1) Treat consistency flags as first-class "failure codes" handled by the decision engine, not as automatic final FLAGGED.
2) Add decision table entries for the consistency flags.
3) Add minimal repair prompt templates referenced by the decision table.
4) Update pipeline finalization to only set FLAGGED when:
   - decision engine ESCALATE occurs, OR
   - max repairs exceeded, OR
   - unresolved high-severity issues remain after repair loop.
(Consistency flags alone should not automatically set final_decision FLAGGED.)

Implementation tasks:

A) Update `spec/decision_table.yaml`
Add entries (exact codes):

healthy_disease_conflict:
  action: REPAIR
  field: disease
  repair_template: repair_disease_from_context_v1
  max_attempts: 2
  fallback_value: "Unknown"
  severity: high

assay_platform_conflict:
  action: REPAIR
  field: data_type
  repair_template: repair_data_type_from_context_v1
  max_attempts: 2
  fallback_value: "Unknown"
  severity: high

single_cell_evidence_missing:
  action: REPAIR
  field: data_type
  repair_template: repair_data_type_from_context_v1
  max_attempts: 2
  fallback_value: "Unknown"
  severity: medium

organism_context_conflict:
  action: ESCALATE
  field: organism
  repair_template: null
  max_attempts: 0
  fallback_value: null
  severity: high

Ensure YAML remains valid.

B) Add new prompt template files:
Create in `prompts/`:

1) `prompts/repair_disease_from_context_v1.txt`
Text should instruct LLM to:
- only return the disease field (as single phrase <=5 words) OR return "Healthy" if no evidence
- must return JSON with exactly keys gse_accession,gsm_accession,disease (or, if you want full schema, keep full 8 keys but focus on disease)
IMPORTANT: For now repair is stubbed, so templates are placeholders. But keep them reasonable for future.

2) `prompts/repair_data_type_from_context_v1.txt`
Similarly, repair data_type using evidence.

Keep templates short and consistent with format validator constraints.

C) Update pipeline behavior in `src/agent/run_single.py`
Specifically in `run_single_from_context_record` and `run_single_gsm` (if applicable):

- You likely convert `consistency_flags` into failures_by_field for the repair loop. Keep doing that (good).
- BUT do NOT set `state.final_decision="FLAGGED"` just because `state.flags` is non-empty.
- Ensure that final_decision is determined mainly by:
  - the result of apply_repairs (it sets final_decision ACCEPT/FLAGGED)
  - or remaining unresolved failures.

Implementation rule:
- After apply_repairs returns, set:
  - if state.final_decision already set by repair loop, keep it.
  - else:
      - if any unresolved failures remain in semantic_errors or ontology_failures -> FLAGGED
      - else -> ACCEPT
- `state.flags` should remain informational unless they represent explicit escalation (like "max_repairs_exceeded") or decision engine escalations.

Also:
- When you add consistency failures into failures_by_field, do NOT also add them into state.flags directly.
  Let decision/repair determine final decision. Keep consistency_flags stored in state.consistency_flags only.

D) Update / verify repair loop behavior (src/agent/repair_loop.py)
Ensure apply_repairs can resolve consistency failures using FALLBACK:
- For REPAIR decisions, your current stub does not change output, so after max attempts, decision engine should move to FALLBACK if fallback_value exists.
- For healthy_disease_conflict, fallback_value is "Unknown". That should replace disease and clear the disease failure.
Implement clearing logic:
- When a decision targets a field (FALLBACK or REPAIR), remove that field’s failures from the local failures_by_field used in the loop, if appropriate.
- Specifically: on FALLBACK, always clear that field’s failures.

If apply_repairs currently does not accept a failures_by_field input and instead reads from state only, adjust carefully:
- It should operate on state.semantic_errors + state.ontology_failures + "consistency failures mapping" stored somewhere.
- Minimal change: in run_single, create a merged failures_by_field and store it onto state temporarily (e.g., state.flags or a new field).
But avoid large refactors. Prefer passing failures_by_field into apply_repairs if it supports it; otherwise update state in a consistent way.

E) Add regression tests
Create `tests/test_consistency_decision_routing.py`

Test 1: healthy_disease_conflict resolved by fallback
- Build a PipelineState with:
  - final_output having disease="Healthy"
  - consistency_flags containing "healthy_disease_conflict"
  - and set up failures_by_field such that decision engine sees disease failure code.
- Call apply_repairs with real decision table loaded from YAML.
- Assert:
  - final_decision == "ACCEPT" (or at least not FLAGGED)
  - final_output["disease"] becomes "Unknown" after fallback

Test 2: organism_context_conflict escalates
- Similar setup for organism_context_conflict
- Assert final_decision == "FLAGGED"

Test 3: end-to-end stub from JSONL does not flag all due solely to healthy_disease_conflict
- Create temp jsonl with context_text containing "cancer" and disease Healthy from stub output.
- Run run_gse_from_jsonl with stub cfg.
- Assert flagged < total (at least one accepted if no organism conflict)

Constraints:
- Keep tests deterministic.
- Use `validator.decision_engine.load_decision_table("spec/decision_table.yaml")`.

After implementation:
- run `uv run python -m pytest -q`

Deliverables:
- updated spec/decision_table.yaml
- new prompts/repair_disease_from_context_v1.txt
- new prompts/repair_data_type_from_context_v1.txt
- updated src/agent/run_single.py (and repair_loop if needed)
- new tests/test_consistency_decision_routing.py
