# Ticket #97: Deterministic Resolution of Cellosaurus Exact-Match Ties

## Background

In real-world GEO datasets, some cell line names produce multiple top-scoring matches in Cellosaurus due to normalization effects.

Example observed:

- Raw cell line: `PC-3`
- Cellosaurus candidates:
  - `CVCL:0035` — label: `PC-3`
  - `CVCL:E2RM` — label: `PC3`

After normalization, both labels are treated as exact matches, resulting in:
- `ontology_ambiguous_cell_line`
- unnecessary LLM repair attempts
- curator-blocking flags despite an obvious correct choice

From a human and curation standpoint, this is not ambiguous.

---

## Problem

The current Cellosaurus matching logic:
- collapses punctuation (`PC-3` vs `PC3`)
- assigns identical top scores
- marks the result as `AMBIGUOUS`

This is overly conservative and introduces noise in otherwise clean annotations.

---

## Proposed Solution

Introduce **deterministic tie-breaking rules** for Cellosaurus matches when multiple candidates share the top score.

These rules apply **only to the `cell_line` field**.

---

## Tie-Breaking Rules (Applied in Order)

When multiple Cellosaurus candidates are tied at the highest score:

### 1. Raw Label Exact Match Preference
Prefer the candidate whose ontology **label exactly matches the raw input string**
(case-insensitive, no normalization beyond casing).

Example:
- raw: `PC-3`
- label `PC-3` → preferred over `PC3`

---

### 2. Punctuation Pattern Match
If no exact raw-label match exists:
- prefer the candidate whose label matches the raw string’s punctuation pattern
  - e.g. presence/absence of hyphens

---

### 3. Minimal Edit Distance
If still tied:
- select the candidate with the smallest edit distance to the raw input
- use a deterministic edit-distance metric

---

### 4. Ambiguity Fallback
Only if all above rules fail to resolve the tie:
- mark the result as `AMBIGUOUS`
- emit `ontology_ambiguous_cell_line`

---

## Matching Outcomes

When a tie is resolved using rules 1–3:

- Mark `cell_line` as:
  - `status = MATCHED`
- Lock the field with:
  - `reason = ontology_terminal_exact`
- Preserve all alternate candidates in audit output for transparency
- Do **not** trigger LLM repair

---

## Audit and Reporting

- Audit record must include:
  - selected Cellosaurus term
  - alternates considered
  - tie-breaking rule used (e.g. `raw_label_exact_match`)
- No curator-facing ambiguity flag if resolution is deterministic

---

## Explicit Non-Goals

This ticket does **NOT**:
- introduce probabilistic selection
- infer cell line identity from disease or tissue
- modify Cellosaurus data
- change canonical schema or output fields

---

## Acceptance Criteria

- `PC-3` resolves deterministically to `CVCL:0035`
- No `ontology_ambiguous_cell_line` flag emitted for this case
- No regression for genuinely ambiguous cell line names
- Behavior is deterministic, explainable, and documented

---

## Rationale

This change:
- aligns machine behavior with curator expectations
- reduces false-positive ambiguity
- preserves conservative handling where ambiguity is real

---

## Priority

Medium–High (curator trust, low risk, localized change)

---

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-97.md` and paste this ticket verbatim.
