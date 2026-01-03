# Checkpoint — 2026-01-02

## Context

This checkpoint records the work leading up to and stabilizing
the first fully functional local-LLM annotation pipeline.

The corresponding stable capability snapshot is documented in:
- `docs/milestones/v0.1-llm.md`

---

## Major Work Completed

- Integrated a real local LLM using HuggingFace Transformers
- Enabled chat-template prompting by default
- Added robust JSON extraction to tolerate fenced/noisy outputs
- Implemented a format repair retry loop
- Implemented decision-based semantic repair using a decision table
- Enabled batch GSE processing via JSONL input
- Verified end-to-end execution with real GEO data

---

## Key Issues Encountered and Resolved

### 1. Noisy LLM Outputs
Small instruction-tuned models frequently returned:
- Markdown code fences
- Extra explanations
- Mixed text + JSON

Resolution:
- Implemented JSON extraction in the format validator
- Validation operates on extracted JSON, not raw text

### 2. Repair Loop Control Flow Bug
Initial repair logic overwrote successful attempts
with later failing attempts.

Resolution:
- Repair loops now stop at the first successful parse
- Only unrepaired failures propagate to FLAGGED

### 3. Overly Strict Consistency Handling
Consistency flags (e.g. healthy vs disease conflict)
were initially treated as fatal.

Resolution:
- Routed consistency flags through the decision engine
- Enabled repair or fallback instead of automatic rejection

### 4. Stub Repair Logic Blocking Real Use
Early repair logic was stubbed and did not call the LLM.

Resolution:
- Enabled LLM-backed repairs returning full schema
- Added bounded retry limits

---

## Observations

- Small models (~1B parameters) can follow format rules
  but struggle with nuanced biological semantics
- Repair loops and fallback values are essential for stability
- Audit logs proved critical for debugging subtle failures

---

## Known Limitations at This Checkpoint

- Ontology grounding not yet implemented
- Assay vs molecule confusion remains common in small models
- No automatic escalation to larger models

---

## Status

- Pipeline is stable
- All samples in test GSEs annotate successfully
- No false FLAGGED results due to formatting noise
