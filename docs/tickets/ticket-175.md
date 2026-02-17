# Ticket #175: Narrow treatment_identity_leakage to avoid wiping real interventions

## Background

Real-world case: GSE165621 / GSM5047039.
LLM extracted treatment "ALDH1B1 KO clone expressing EGFP", but the pipeline deterministically replaced it with "None" and flagged "treatment_not_an_intervention".

Artifacts:
- audit.jsonl shows locked_fields.treatment reason "treatment_not_an_intervention"
- final_output.treatment is "None"
- evidence.jsonl has treatment flag ["treatment_not_an_intervention"]

## Problem Statement

The semantic rule that triggers failure code `treatment_identity_leakage` (mapped to deterministic fallback to None + flag `treatment_not_an_intervention`) is too strict.
It incorrectly treats common genetic perturbation / clone descriptors as “identity leakage”, causing loss of valid treatment information.

This is a policy-level semantic issue, not an LLM repair issue.

## Proposed Change

Update the semantic validation logic for `treatment_identity_leakage`:

1. Add a deterministic allowlist of “intervention indicators” for genetic/construct perturbations.
2. If the treatment string contains any allowlisted intervention indicators, do NOT emit `treatment_identity_leakage`.
3. Preserve current behavior (emit `treatment_identity_leakage` and deterministic fallback to `None` with flag `treatment_not_an_intervention`) when intervention indicators are absent.

Initial allowlist (minimum set, can be extended only with additional real-world evidence):
- KO / knockout / KD / knockdown
- CRISPR / sgRNA / shRNA / siRNA
- overexpress / OE / expressing
- transduced / transfected
- clone / stable
- lentivirus / plasmid / vector
- GFP / EGFP

No new LLM calls. No ontology grounding changes.

## Policy Impact

* [ ] No policy change
* [ ] Policy clarification only
* [x] Policy change (policy-spec.md must be updated)

Update `policy-spec.md` Section 3 (treatment) to clarify that
`treatment_identity_leakage` must NOT fire when intervention indicators
are present (genetic perturbation / construct descriptors).

## Acceptance Criteria

1. For GSM5047039, final_output.treatment remains "ALDH1B1 KO clone expressing EGFP".
2. For GSM5047039, evidence.jsonl for treatment has no "treatment_not_an_intervention" flag.
3. Determinism preserved: repeated runs yield identical results.
4. Existing identity-leakage cases (sample IDs / replicate labels / accessions) still trigger `treatment_identity_leakage` and fallback to "None".

## Non-Goals

- No treatment ontology grounding.
- No attempt to normalize or structure treatment strings.
- No UI reinterpretation of treatment flags.

## Constraints

- Do not invent future behavior without evidence.
- Prefer deterministic rules over additional LLM calls.
- Prefer flagging over silent correction when ambiguity is high.
- Human curation must remain explicit and auditable.

## Guiding Principle

Policies are written consequences of code, not aspirations.
If behavior changes, policy documentation must change with it.

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-175.md` and paste this ticket verbatim.
