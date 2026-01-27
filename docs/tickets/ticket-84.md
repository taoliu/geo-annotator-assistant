# Ticket #84: Disease Modifier Generalization Policy (DOID + NCIT)

## Milestone
v0.9 — Validation, Repair, and Reporting Consolidation

## Type
Policy consolidation / backend logic refinement

## Status
Approved (policy locked)

---

## Summary

Implement a deterministic **Disease Modifier Generalization** policy that generalizes modifier-enriched disease strings (e.g. molecular-driver annotations) to ontology-supported parent disease terms when a clear parent exists, avoiding unnecessary repair loops and FLAGGED outcomes.

This policy explicitly supports **both Human Disease Ontology (DOID) and NCI Thesaurus (NCIT)** as first-class cancer ontologies.

---

## Motivation

Real-world cancer datasets frequently describe disease using modifier-enriched phrases such as:

- "Kras-driven lung cancer"
- "EGFR-mutant lung adenocarcinoma"
- "TP53-null breast cancer"

These phrases are biologically meaningful but are **not ontology disease labels** in DOID or NCIT. Under v0.8 behavior, such cases often:

- trigger `ontology_low_confidence_disease`
- enter repair loops that do not converge
- produce large numbers of FLAGGED GSMs

This degrades curator trust while providing no increase in correctness.

The goal is to **generalize conservatively** to a supported ontology parent while preserving specificity in audit records.

---

## Policy Definition (Authoritative)

### Disease Modifier Generalization Rule

When **all** of the following conditions hold:

1. Field is `disease`
2. Ontology grounding status is `LOW_CONFIDENCE`
3. Ontology alternates (from DOID and/or NCIT) include a **parent disease term** that:
   - is ontology-valid (DOID or NCIT)
   - has the highest confidence score after applying existing ranking rules
4. The parent disease label is a **literal substring** of the raw disease string  
   (case-insensitive, hyphen/space normalized)

Then:

- The canonical `disease` value **MUST** be set to the selected parent disease label
- The selected ontology term **MUST** be locked as terminal
- Ontology grounding for `disease` is considered **resolved via generalization**
- **Repair MUST NOT be triggered** for this condition
- Final decision **MUST** be `ACCEPT`
- An **informational flag** MUST be emitted

This rule is deterministic and loss-minimizing.

---

## Ontology Scope and Selection Rules

- **Both DOID and NCIT MUST be considered** when identifying parent disease candidates
- Parent selection follows existing ontology ranking and tie-breaking rules:
  1. Exact or normalized label match
  2. Higher confidence score
  3. Deterministic tie-break (existing preference rules apply)
- The selected parent term may come from **either DOID or NCIT**
- The chosen ontology source MUST be recorded in canonicalization and locking metadata

---

## Reporting Semantics

### Canonical Output
- `final_output.disease` = generalized parent disease label (e.g. `lung cancer`)
- Parent ontology term is terminally locked

### Flags
- Emit informational flag:  
  **`disease_generalized_for_ontology`**

**Flag meaning**:  
> Raw disease contained non-ontology modifiers; canonical disease generalized to closest ontology-supported parent.

This flag:
- is curator-visible
- does not trigger repair
- does not cause FLAGGED decisions

### Audit Preservation
- Original LLM disease phrase MUST remain visible in:
  - `raw_value`
  - `llm_parsed_outputs`
  - ontology match audit fields

No information is discarded.

---

## Explicit Non-Goals

This policy does **NOT**:

- Add ontology synonyms
- Treat modifier-enriched strings as valid ontology labels
- Apply to fields other than `disease`
- Apply when no clear parent candidate exists
- Apply when parent label is not literally contained in raw string
- Introduce fuzzy semantic collapsing beyond deterministic containment
- Change schema, UI, or learning behavior

If the conditions are not met, existing v0.8 behavior remains unchanged.

---

## Implementation Notes (Non-Prescriptive)

- Apply after ontology grounding and before repair triggering
- Use existing `alternates` ranking output
- Substring containment must be strict and deterministic
- Suppress `ontology_low_confidence_disease` as a failure when generalization applies
- Replace failure with informational flag only

---

## Tests to Add

- Disease `"Kras-driven lung cancer"` → canonical `"lung cancer"` → ACCEPT
- Ensure no repair attempts recorded for disease
- Ensure original raw disease phrase preserved in audit
- Ensure behavior unchanged when:
  - no parent substring exists
  - no ontology parent candidate exists

---

## Expected Impact

- Significant reduction in unnecessary `ontology_low_confidence_disease` failures
- Fewer repair loops with no convergence
- Improved consistency across GSMs within a GSE
- Increased curator trust without weakening ontology guarantees

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-84.md` and paste this ticket verbatim.
