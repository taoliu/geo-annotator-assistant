# Ticket #85: Clarify `tissue_type` Semantics as Disease Site in LLM Prompt

## Milestone
v0.9 — Validation, Repair, and Reporting Consolidation

## Type
Policy clarification / prompt-level constraint

## Status
Proposed (policy-level, no code yet)

---

## Summary

Clarify the semantic meaning of the `tissue_type` field at the **LLM prompt level** to ensure it consistently represents the **anatomical site of the disease or experimental context**, not the developmental origin or lineage of sampled cells.

This change reduces ambiguity upstream and prevents unnecessary downstream flags or normalization.

---

## Motivation

Real-world cancer datasets frequently describe samples using phrases such as:

- bone-marrow-derived tumor-associated macrophages
- infiltrating immune cells
- lineage-specific cell origins

For solid tumors, these descriptions create ambiguity for `tissue_type`, leading LLMs to alternate between:

- anatomical disease site (e.g. lung)
- cell lineage or origin (e.g. bone marrow)

Both interpretations are biologically valid, but **only one is canonical** under the current schema.

v0.8 behavior implicitly treats `tissue_type` as the **anatomical disease site**, but this is not made explicit in the LLM prompt, resulting in inconsistent outputs within the same GSE.

---

## Policy Definition (Authoritative)

For LLM extraction:

> `tissue_type` MUST represent the **anatomical tissue or organ associated with the disease or experimental context**, not the developmental origin, lineage, or source of the sampled cells.

### Examples (authoritative guidance)

- Tumor-associated macrophages in lung cancer  
  → `tissue_type = lung`

- Bone-marrow-derived immune cells infiltrating lung tumors  
  → `tissue_type = lung`

- Hematopoietic malignancy (e.g. leukemia, myeloma)  
  → `tissue_type = bone marrow`

This rule applies **only at the semantic interpretation level** and does not change schema or ontology logic.

---

## Required Prompt Change

Update the LLM prompt prefix to include the following clarification block **verbatim or semantically equivalent**:

```text
Important clarification:
- tissue_type MUST represent the anatomical tissue or organ associated with the disease or experimental context.
- Do NOT use cell lineage, developmental origin, or cell source (e.g. bone marrow–derived, immune lineage) as tissue_type unless the disease itself is a hematopoietic disease.

Examples:
- Tumor-associated macrophages in lung cancer → tissue_type = "lung"
- Bone-marrow-derived immune cells infiltrating lung tumors → tissue_type = "lung"
- Leukemia or bone marrow malignancy → tissue_type = "bone marrow"
```

The remainder of the prompt, output schema, and rules MUST remain unchanged.

---

## Scope

IN SCOPE:

* LLM prompt text clarification only
* Semantic disambiguation for `tissue_type`

OUT OF SCOPE:

* Schema changes
* Validator or ontology logic changes
* Repair policy changes
* Introduction of new fields (e.g. cell origin)
* UI changes
* Heuristic post-processing

---

## Reporting and Validation Impact

* This change is expected to **reduce ambiguity upstream**
* It should **lower the incidence of conflicting tissue_type predictions** within a GSE
* It does NOT introduce new validation rules
* Any remaining ambiguity is handled by existing v0.8 validation behavior

---

## Tests to Add (Minimal)

* Prompt snapshot or golden-text test asserting the presence of the clarification block
* Ensure prompt text regression is detectable

No LLM behavior tests are required.

---

## Non-Goals

This ticket does NOT:

* Encode both tissue site and origin in `tissue_type`
* Allow compound or parenthetical tissue values
* Attempt automatic reconciliation downstream
* Modify disease, cell_line, or treatment semantics

---

## Rationale

Upstream semantic clarity is preferred over downstream heuristics.
This policy preserves determinism, curator trust, and architectural simplicity while remaining consistent with v0.8 assumptions.

---

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-85.md` and paste this ticket verbatim.
