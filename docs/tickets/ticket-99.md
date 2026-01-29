# Ticket #99: Generate and Maintain a Unified Policy Specification Document

## Title
AGENT-POLICY-099 — Create `docs/policies/policy-spec.md` by reviewing current codebase and summarizing all active policies

## Background / Motivation
By v0.9, the system has accumulated a large number of **implicit policies** governing:
- disease generalization and normalization
- tissue type handling (anatomical vs non-anatomical placeholders)
- ontology grounding (DOID, NCIT, UBERON, Cellosaurus, EFO)
- validation failures, flags, and final decisions
- repair loops, deterministic fallbacks, and human-curation triggers

These rules are currently encoded across validators, ontology matchers, repair templates, and decision logic, but **are not written down in one authoritative document**.

This makes reasoning, onboarding, and future refactoring difficult.

We need a **descriptive, code-as-truth policy document** that reflects *current behavior only*, without introducing new logic.

## Scope
This ticket is **documentation-only**.
No behavior changes, no refactors, no renaming.

The document must summarize **all policies currently enforced in code**, including those introduced *before* Ticket #84.

## Deliverable
Create a new document:

```
docs/policies/policy-spec.md
```

This document becomes the **single canonical description of current annotation policy behavior**.

## Required Content Structure

### 1. Overview
- Purpose of the policy spec
- Explicit statement: “This document describes current behavior. Code is authoritative.”

### 2. Pipeline Stages and Precedence
Describe the execution order, for example:
1. LLM raw output
2. Format validation
3. Ontology grounding
4. Semantic validation
5. Repair loop (LLM or deterministic)
6. Terminal fallback
7. Final decision (ACCEPT / FLAGGED / REJECT)

Include precedence rules when multiple failures exist.

### 3. Field-by-Field Policy Rules
For each field (`data_type`, `organism`, `tissue_type`, `cell_line`, `disease`, `treatment`):

- Allowed value types
- Ontology sources used
- What constitutes:
  - MATCHED
  - LOW_CONFIDENCE
  - AMBIGUOUS
  - FALLBACK
- When the field becomes **locked**
- When human curation is required

### 4. Disease-Specific Policies
Document all active disease rules, including:
- Deterministic generalization (e.g. “lung tumor” → “lung cancer”)
- Handling of modifiers (relapsed, refractory, high-grade, serous)
- Healthy / Unknown / Not sure handling
- Model vs true disease distinction
- DOID vs NCIT selection rules and tie-breaking

### 5. Tissue Type Policies
- Anatomical tissue requirements
- Non-anatomical placeholders (e.g. Tumor, Lymphoma, Blood-derived disease names)
- When tissue is replaced with `Unknown`
- When tissue errors are flagged vs auto-corrected

### 6. Cell Line Policies
- Exact match vs ambiguous match handling
- Preference rules (e.g. PC-3 vs PC3)
- When ambiguity is auto-resolved vs flagged

### 7. Failure Codes and Flags
Produce a table listing **all**:
- failure codes
- flags
- meanings
- triggering conditions
- where implemented (file + function)

Examples:
- `ontology_low_confidence_disease`
- `disease_inferred_without_evidence`
- `ontology_ambiguous_cell_line`
- `repair_template_missing`

### 8. Repair Templates and Fallbacks
For each repair mechanism:
- Name of template
- Trigger condition
- Whether LLM is used
- Deterministic vs non-deterministic
- Max retry behavior
- Terminal fallback behavior

### 9. Final Decision Logic
Explain clearly:
- ACCEPT vs FLAGGED vs REJECT
- Which failures are blocking
- Which are informational
- Role of terminal fallback fields

### 10. Traceability Notes
- When a rule originated from a known ticket, list it
- Otherwise mark as “pre-v0.9 legacy behavior”

## Method (How to Do This)
Codex should:
1. Search the codebase for:
   - failure codes
   - flags
   - repair templates
   - decision logic
2. Treat code as ground truth
3. Write the document **after** reviewing code, not from memory
4. Avoid speculation or future design

## Acceptance Criteria
- `docs/policies/policy-spec.md` exists
- Document covers all fields and failure modes currently in code
- No behavior changes introduced
- Document is readable, structured, and precise
- Future tickets can reference this document as policy authority

## Non-Goals
- No new policies
- No refactoring
- No automatic doc generation pipeline (manual for now)

## Follow-ups (Out of Scope)
- Optional: per-milestone policy diffs
- Optional: auto-validation that policy doc is updated when new failure codes are added

---

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-99.md` and paste this ticket verbatim.
