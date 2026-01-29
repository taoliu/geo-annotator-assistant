# Ticket #95: Non-Anatomical Tissue Placeholder Registry and Unified Handling

## Background

After Ticket #94, disease-derived strings (e.g. “Lymphoma”) are correctly prevented from being interpreted as anatomical `tissue_type`.  
However, the handling logic for non-anatomical tissue values is currently fragmented across multiple checks and flags, including:

- "Tumor" placeholder handling
- disease-term leakage into `tissue_type`
- ad hoc LOW_CONFIDENCE ontology failures
- repeated LLM repair attempts that cannot succeed

This leads to:
- duplicated logic
- inconsistent flags
- unnecessary ontology grounding and LLM calls
- reduced curator clarity

---

## Problem

`tissue_type` is defined to represent **anatomical source only** (Uberon-aligned).  
Non-anatomical strings (disease names, pathological states, abstract labels) must be handled deterministically and consistently.

Examples observed in real data:
- Tumor
- Lymphoma
- Cancer
- Neoplasm
- Leukemia
- Metastasis
- Lesion
- Malignancy

These values:
- are not Uberon anatomy
- should never trigger ontology grounding
- should never trigger LLM repair
- should be curator-visible but not destructive

---

## Proposed Solution

Introduce a **Non-Anatomical Tissue Placeholder Registry** with unified handling.

### 1. Registry Definition

Create a deterministic registry (static list or regex-based) for non-anatomical tissue placeholders, including but not limited to:

- tumor / tumour
- cancer
- carcinoma
- neoplasm
- malignancy
- lymphoma
- leukemia
- myeloma
- metastasis
- lesion

The registry must be:
- deterministic
- version-controlled
- documented

---

### 2. Unified Handling Logic

When `tissue_type` matches the registry:

- **Do NOT attempt Uberon grounding**
- **Do NOT attempt LLM repair**
- Set:
  - `tissue_type = "Unknown"`
- Lock the field with:
  - `reason = tissue_type_non_anatomical_placeholder`
  - preserve `original_value` in audit
- Emit a single, consistent flag:
  - `tissue_type_non_anatomical_placeholder`

---

### 3. Reporting and Audit Semantics

- `ontology_status_by_field.tissue_type = "FALLBACK"`
- `matched_via = non_anatomical_placeholder`
- Exactly one flag emitted (no LOW_CONFIDENCE noise)
- Clear curator signal:
  - tissue context ambiguous or disease-derived
  - manual review may be needed

---

### 4. Explicit Non-Goals

This ticket does **NOT**:
- infer anatomical site from disease
- generalize tissue based on other GSMs
- introduce learning or cross-sample inference
- change the canonical 8-field schema

---

## Acceptance Criteria

- All known non-anatomical tissue strings are handled by the registry
- No Uberon grounding attempted for registry matches
- No LLM repair attempts for registry matches
- Exactly one deterministic flag per affected GSM
- No regression in previously accepted anatomical tissues
- Behavior is fully documented in audit output

---

## Rationale

This consolidation:
- reduces code duplication
- stabilizes curator-facing behavior
- prevents futile repairs
- aligns with v0.9 goals of policy hardening and clarity

This ticket prepares the ground for future UI or reporting improvements without changing core semantics.

---

## Priority

High (policy consolidation, low implementation risk)

---

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-95.md` and paste this ticket verbatim.
