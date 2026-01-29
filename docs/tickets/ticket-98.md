# Ticket #98: Deterministic Handling of LLM Non-Answer Placeholders

## Background

In real-world GEO metadata, LLMs sometimes explicitly express uncertainty rather than hallucinating a value.  
Common examples observed:

- `Not sure`
- `Not clear`
- `Unknown`
- `Unclear`
- `N/A`
- `Not provided`
- `?`

Example (GSE309061):

```
"disease": "Not sure"
```

These are **non-answers**, not low-confidence disease terms.  
Current behavior incorrectly:
- passes them into ontology grounding
- produces meaningless alternates
- triggers repair loops
- emits misleading curator flags

---

## Problem

LLM non-answer placeholders are currently treated as candidate values, which:
- pollutes ontology matching
- wastes repair attempts
- reduces curator trust
- obscures the fact that the LLM explicitly declined to infer a value

---

## Proposed Solution

Introduce a **deterministic, pre-ontology validation rule** that detects LLM non-answer placeholders and handles them explicitly.

---

## Non-Answer Placeholder Detection

Define a normalized (case-insensitive, trimmed) set including:

- `unknown`
- `not sure`
- `not clear`
- `unclear`
- `n/a`
- `na`
- `none`
- `not provided`
- `?`

Detection must occur **before ontology grounding and repair**.

---

## Field-Specific Handling Rules

### Disease
When a non-answer placeholder is detected:

- Set:
  - `disease = "Unknown"`
- Lock field with:
  - `reason = llm_non_answer_placeholder`
- Emit flag:
  - `llm_non_answer_disease`
- Skip:
  - ontology grounding
  - LLM repair attempts

---

### Treatment
- Set:
  - `treatment = "None"`
- Lock with:
  - `llm_non_answer_placeholder`
- No repair

---

### Tissue Type
- Set:
  - `tissue_type = "Unknown"`
- Lock with:
  - `llm_non_answer_placeholder`
- Emit:
  - `llm_non_answer_tissue_type`

---

### Cell Line
- Set:
  - `cell_line = "Unknown"`
- Lock with:
  - `llm_non_answer_placeholder`
- Emit:
  - `llm_non_answer_cell_line`

---

### Other Fields (organism, data_type)
- Set to:
  - `Unknown`
- Lock with:
  - `llm_non_answer_placeholder`

---

## Audit and Reporting

- Preserve original raw value in audit
- Record:
  - placeholder detection trigger
  - field-specific fallback applied
- No ontology alternates generated
- No repair history entries created

---

## Explicit Non-Goals

This ticket does **NOT**:
- attempt to infer missing values
- use LLM to clarify uncertainty
- change canonical output schema
- reinterpret “unknown” as a real ontology term

---

## Acceptance Criteria

- `"Not sure"` never reaches ontology matching
- No alternates are generated for placeholder values
- No repair loops triggered for placeholders
- Curator-facing flags clearly distinguish:
  - LLM uncertainty vs ontology mismatch
- Behavior is deterministic and documented

---

## Rationale

This change:
- respects explicit LLM uncertainty
- reduces noise and false flags
- improves audit clarity
- aligns with v0.9 goals of correctness and curator trust

---

## Priority

High (data quality, low risk, deterministic)

---

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-98.md` and paste this ticket verbatim.
