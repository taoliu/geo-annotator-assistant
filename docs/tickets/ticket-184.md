# Ticket #184: Treat "mesothelioma" as oncology trigger and normalize to malignant mesothelioma (NCIT)

## Background

Case: GSE212521 / GSM6533923

LLM disease: "Mesothelioma"

Audit:
- DOID match status = LOW_CONFIDENCE (jaccard 0.5, no exact label/synonym hit)
- ncit_fallback_enabled = true but ncit_triggered = false
- selection_rule = "ncit_trigger_false"
- final_decision = FLAGGED with ontology_low_confidence_disease

This occurs because:
1) "mesothelioma" does not trigger NCIT fallback under current trigger terms
2) DOID contains specific mesothelioma subtypes but the generic term is not resolved deterministically
3) We want generic "mesothelioma" to resolve to the standard malignant concept in NCIT

## Problem Statement

Generic disease term "mesothelioma" is common in GEO metadata.
Current logic fails to:
- trigger NCIT fallback for this oncology term
- deterministically map the generic term to a canonical malignant mesothelioma concept

This causes unnecessary LOW_CONFIDENCE outcomes and FLAGGED decisions.

## Proposed Change

### A) Expand NCIT oncology trigger terms

Add "mesothelioma" to the NCIT trigger list used for disease fallback.
This ensures NCIT search is attempted when disease query contains "mesothelioma".

### B) Deterministic canonicalization rule for generic "mesothelioma"

Before ontology lookup (or as an early deterministic rewrite step in disease matching):

If disease value (normalized) is exactly:
- "mesothelioma"
or matches a small set of equivalent forms:
- "mesothelioma (unspecified)"
- "mesothelioma, unspecified"

Then rewrite the query to:
- "mesothelioma, unspecified"

Rationale:
- This phrase is expected to match NCIT synonyms for malignant mesothelioma.

### C) Source preference for this case

When the rewritten query is used:
- Prefer NCIT match if it yields an exact label/synonym match.
- Output should canonicalize to the NCIT preferred label:
  - "Malignant Mesothelioma" (NCIT:C4456)

No new LLM calls.

## Policy Impact

[x] Policy update required.

Update policy-spec.md:
- Add "mesothelioma" to oncology trigger terms for NCIT fallback.
- Add deterministic disease rewrite rule:
  - "mesothelioma" -> "mesothelioma, unspecified"
- Specify that in this rewrite case, NCIT exact match takes priority over DOID similarity matches.

No whitepaper change required.

## Acceptance Criteria

1) GSM6533923:
- disease resolves as MATCHED in NCIT
- matched_term_id = NCIT:C4456
- matched_label = "Malignant Mesothelioma"
- match_type is exact (label_norm_exact or synonym_norm_exact)
- ncit_triggered = true and attempted_sources includes "NCI Thesaurus"
- no ontology_low_confidence_disease flag
- final_decision is no longer FLAGGED due to disease

2) Determinism:
- reruns produce identical outputs.

3) Regression:
- Mesothelioma subtypes (e.g., "peritoneal mesothelioma") should continue to resolve normally
  (prefer exact DOID if exact exists, otherwise allow NCIT fallback).
- Other disease terms unchanged.

## Non-Goals

- No broad oncology ontology refactor.
- No ingestion changes.
- No UI changes.

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-184.md` and paste this ticket verbatim.
