# Ticket #96: Disease Grounding Token-Equivalence for Oncology Synonyms

## Background

In multiple real-world GEO datasets, disease strings provided by submitters or inferred by LLMs are biologically correct but fail to reach terminal ontology match thresholds due to **string-level variation**, not semantic mismatch.

Example observed:

- Raw disease:  
  `High-grade serous ovarian cancer`
- NCIT label:  
  `Ovarian High Grade Serous Adenocarcinoma` (NCIT:C105555)

Despite clear semantic equivalence, grounding currently yields:
- `LOW_CONFIDENCE`
- repeated LLM repair attempts
- curator-facing flags that suggest uncertainty where none exists

This reduces curator trust, especially in oncology datasets.

---

## Problem

Current disease grounding relies on token-based similarity (e.g., Jaccard), which is brittle to:

- word order differences
- hyphenation (`high-grade` vs `high grade`)
- oncology synonym variation (`cancer` vs `adenocarcinoma`)

As a result, semantically equivalent cancer terms fail to achieve terminal match status.

---

## Proposed Solution

Introduce a **deterministic, oncology-scoped token-equivalence normalization layer** for disease grounding **before similarity scoring**, applied only to DOID/NCIT disease matching.

---

## Scope

**Applies only to:**
- `field = disease`
- ontology sources: DOID and NCIT
- similarity-based matching paths (non-exact)

**Does NOT apply to:**
- tissue_type
- data_type
- cell_line
- non-disease fields
- non-oncology terms

---

## Token Equivalence Rules

Treat the following tokens as interchangeable *for similarity scoring only*:

### Core oncology equivalence class
- `cancer`
- `carcinoma`
- `adenocarcinoma`
- `neoplasm`
- `malignancy`

### Optional spelling normalization
- `tumor` ≈ `tumour`

### Pre-normalization
- lowercase
- strip punctuation
- normalize hyphens (`high-grade` → `high grade`)

These transformations must be:
- deterministic
- reversible (original string preserved in audit)
- explicitly documented

---

## Matching Behavior

After token-equivalence normalization:

- Recompute similarity score
- If score ≥ terminal threshold:
  - Mark as `MATCHED`
  - `match_type = token_equiv_similarity`
  - Lock disease field
- Preserve alternates and original scores in audit

---

## Audit and Reporting

- Original raw disease string remains unchanged
- Ontology match record must include:
  - original score
  - post-equivalence score
  - equivalence class used
- No LLM repair attempts triggered if terminal match achieved

---

## Explicit Non-Goals

This ticket does **NOT**:
- introduce new disease inference
- generalize model names to diseases
- use LLMs for repair or confirmation
- change canonical schema or field semantics
- apply heuristics outside oncology

---

## Acceptance Criteria

- `High-grade serous ovarian cancer` grounds to:
  - NCIT:C105555
  - status: MATCHED
  - no repair attempts
  - no curator flag
- No regression for non-cancer diseases
- Behavior is deterministic and documented
- All changes confined to disease grounding logic

---

## Rationale

This change reflects real biomedical usage while preserving system conservatism.

It improves:
- curator trust
- oncology dataset quality
- signal-to-noise ratio in flags

without introducing hidden semantics or learning.

---

## Priority

High (oncology correctness, low risk, deterministic)

---

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-96.md` and paste this ticket verbatim.
