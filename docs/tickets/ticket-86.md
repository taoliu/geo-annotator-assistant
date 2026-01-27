# Ticket #86: Prevent Global Record Fallback on Unrepaired Format Errors

## Milestone
v0.9 — Validation, Repair, and Reporting Consolidation

## Type
Correctness bug fix / decision logic hardening

## Status
Proposed (high priority)

---

## Summary

Fix a critical bug where **unrepaired format errors** (e.g. word limit violations) trigger a **global record fallback**, causing valid and locked fields to be overwritten with `Unknown`, `Healthy`, or other defaults.

Fallback behavior must be **field-local** unless the entire record is structurally unrecoverable.

---

## Motivation

In real-world datasets (example: `GSE190105 / GSM5714226`), a single unrepaired format error resulted in:

- valid ontology-matched fields being erased
- locked fields being ignored
- disease replaced with `Healthy`
- multiple fields replaced with `Unknown`
- final output appearing “clean” but biologically wrong

This violates v0.8 architectural invariants and severely undermines curator trust.

---

## Observed Failure Pattern (Reference Case)

From audit log:

- `data_type`: MATCHED and terminal (EFO)
- `organism`: correctly inferred
- `cell_line`: valid fallback
- `tissue_type`: LOW_CONFIDENCE
- `disease`: LOW_CONFIDENCE
- `format_errors`: `["word_limit_violation"]` (treatment field)

Despite only a **single unrepaired format error**, the final output became:

```json
{
  "data_type": "Unknown",
  "organism": "Unknown",
  "tissue_type": "Unknown",
  "cell_line": "No",
  "disease": "Healthy",
  "treatment": "None"
}
```

This is unacceptable.

---

## Policy Definition (Authoritative)

### Record Fallback Rule

Global record fallback (i.e. replacing multiple fields with default values such as `Unknown`, `Healthy`, `None`) MUST occur **only** when:

* the JSON structure is invalid or unrecoverable, OR
* required keys are missing and cannot be reconstructed

### Format Error Handling Rule

* **Format errors are field-local**
* An unrepaired format error MUST:

  * affect only the offending field
  * produce a field-level fallback or flag
* It MUST NOT:

  * overwrite unrelated fields
  * discard locked ontology matches
  * trigger record-wide defaulting

---

## Required Behavior Changes

1. **Preserve validated fields**

   * Fields with successful validation or ontology locks MUST remain intact regardless of other field failures.

2. **Localize format failure impact**

   * If a format error is unrepaired:

     * flag the record
     * apply fallback only to that field
     * keep original or repaired values for other fields

3. **Disallow implicit global resets**

   * `Unknown`, `Healthy`, `None` MUST NOT be injected globally unless explicitly justified by schema-level failure.

4. **Final decision semantics**

   * Such records should be `FLAGGED`, not silently rewritten.

---

## Scope

IN SCOPE:

* Decision routing logic
* Final output construction
* Interaction between format validation, repair status, and fallback
* Preservation of locked fields

OUT OF SCOPE:

* Tissue type semantic policy
* Disease ontology policies
* Prompt changes
* UI changes
* Schema changes

---

## Implementation Notes (Non-Prescriptive)

* Review decision logic in:

  * decision engine
  * writer / final output assembly
* Identify any “format_unrepaired → global fallback” short-circuit
* Enforce field-local fallback semantics
* Ensure locked fields are immutable once set

---

## Tests to Add

* Regression test using GSM5714226-like pattern:

  * One unrepaired format error
  * Multiple validated fields
  * Assert no global fallback occurs
* Test that locked fields survive unrelated failures
* Test that final decision is `FLAGGED`, not `ACCEPT`

---

## Non-Goals

This ticket does NOT:

* Relax format rules
* Change what constitutes a format error
* Modify repair prompts
* Introduce new fallback values
* Alter disease or tissue semantics

---

## Rationale

A partially correct, flagged record is always preferable to a clean but wrong record.
This fix restores v0.8 guarantees of locality, determinism, and curator trust.

---

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-86.md` and paste this ticket verbatim.
