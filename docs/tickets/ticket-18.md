# Ticket #18: AGENT-WS-018 — Repair-first handling for “inferred without evidence” (disease + cell_line), then escalate

You are working in repo `geo-gsm-annotator-agent`.

## Context

We observed cases where the LLM outputs **plausible but unsupported values** for:

* `disease` (e.g. hepatocellular carcinoma)
* `cell_line` (e.g. HepG2)

even though the input `context_text` does **not explicitly contain evidence** for these fields.

The semantic validator correctly emits errors such as:

* `disease_inferred_without_evidence`
* (to be added) `cell_line_inferred_without_evidence`

Currently, these errors lead directly to `final_decision = FLAGGED`.

Project preference: **attempt LLM repair first**, enforcing strict evidence rules, and **only escalate if repair still fails**.

---

## Goal

1. Route `*_inferred_without_evidence` errors for `disease` and `cell_line` to a **repair step first**.
2. Use evidence-strict repair prompts that instruct the LLM to remove unsupported fields.
3. Re-run validators after repair.
4. Escalate only if repair still produces unsupported values.
5. Preserve full auditability of attempts and decisions.

---

## Non-goals

* Do not change the 8-field output schema.
* Do not weaken semantic validation rules.
* Do not change ontology grounding logic or thresholds.
* Do not infer disease or cell line implicitly from ontology or general knowledge.

---

## Tasks

### A) Add semantic failure codes for evidence inference

Files:

* `src/validator/semantic_validator.py`
* `src/validator/failure_codes.py`

Actions:

1. Ensure `disease_inferred_without_evidence` is surfaced as a stable failure code used by the decision engine.
2. Add a new semantic error and failure code:

   * `cell_line_inferred_without_evidence`
3. These errors should be emitted **only when the value is not explicitly supported by `context_text`**.

---

### B) Update decision routing to REPAIR first

Files:

* `spec/decision_table.yaml`

Actions:

* Add decision rules so that:

  * `DISEASE_INFERRED_WITHOUT_EVIDENCE` → `REPAIR` (field = `disease`)
  * `CELL_LINE_INFERRED_WITHOUT_EVIDENCE` → `REPAIR` (field = `cell_line`)

Ensure these routes take precedence over immediate FLAG.

---

### C) Add evidence-strict repair prompts

Create two new prompt files:

1. `prompts/repair_disease_evidence_v1.txt`
2. `prompts/repair_cell_line_evidence_v1.txt`

Prompt requirements (both):

* Input:

  * original `context_text`
  * current predicted JSON
* Instructions:

  * Only keep the field if it is **explicitly supported** by the context.
  * If no explicit evidence exists, output the canonical null value (use the project’s existing convention, e.g. `"No"`).
  * Do **not** infer from general biological knowledge.
  * Do **not** change other fields unless they are invalid.
  * Output must be valid JSON with all 8 required fields.

---

### D) Wire new repair routes into the repair loop

Files:

* `src/agent/repair_loop.py`
* `src/agent/prompts.py` (or prompt registry)

Actions:

1. Register the two new prompts.
2. Route failures:

   * `DISEASE_INFERRED_WITHOUT_EVIDENCE` → `repair_disease_evidence_v1`
   * `CELL_LINE_INFERRED_WITHOUT_EVIDENCE` → `repair_cell_line_evidence_v1`
3. Ensure repair attempts are recorded in:

   * `repair_history`
   * `attempts_by_field`

---

### E) Escalation rule after repair

Files:

* `src/agent/repair_loop.py`
* `src/validator/decision_engine.py` (if escalation is handled there)

Policy:

* Maximum 1 repair attempt per field for evidence-based errors.
* After repair:

  * Re-run format, semantic, and ontology validation.
  * If the same `*_inferred_without_evidence` error persists:

    * Escalate to `FLAGGED` (or `REJECTED`, if that is the existing strict policy).
    * Preserve the failure flag in `final_decision`.

---

### F) Tests (LLM-stubbed)

Files:

* `tests/test_repair_inferred_without_evidence.py`

Test cases:

1. Disease inferred without evidence:

   * Initial semantic error triggers REPAIR.
   * Stubbed repair removes disease → no disease evidence error remains.
2. Cell line inferred without evidence:

   * Initial semantic error triggers REPAIR.
   * Stubbed repair removes cell line → error resolved.
3. Escalation:

   * Stubbed repair returns the same unsupported value.
   * Pipeline escalates with final FLAGGED decision.
4. Audit integrity:

   * Repair attempts and decisions are recorded correctly.

---

## Acceptance criteria

* For records where `disease` or `cell_line` are hallucinated:

  * The pipeline attempts repair before flagging.
* If repair removes unsupported fields, the evidence error disappears.
* If repair fails, the run escalates deterministically.
* Audit output clearly shows:

  * original output
  * repair attempt
  * final decision
* `pytest -q` passes.

---

## Ticket file requirement (MANDATORY)

After generating this ticket, the AI coding agent **must create**:

```
docs/tickets/ticket-18.md
```

and copy **the full contents of this ticket verbatim** into that file.
