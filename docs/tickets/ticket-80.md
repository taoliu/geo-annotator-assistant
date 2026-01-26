# Ticket #80: Extend Sample Title context_fingerprint normalization with keyword-anchored ID/replicate patterns (conservative)

## Problem

Some replicate-like GSMs differ only in Sample Title by embedded identifiers (patient/donor/subject IDs) or explicit replicate markers, preventing per-GSE cache hits even when semantic evidence is identical.

We want a conservative normalization that targets only high-confidence ID/replicate patterns.

## Scope (minimal, deterministic)

Update context_fingerprint normalization applied only to the `Sample Title:` line to handle:

1. Keyword-anchored IDs:
   * Normalize IDs immediately following (case-insensitive): `patient`, `donor`, `subject`
   * Examples:
     * `donor_001` -> `donor_<ID>`
     * `PTL_patient_R-27_1` -> `PTL_patient_<ID>_1`

2. Explicit replicate markers (case-insensitive):
   * `rep`, `replicate`, `biorep`, `bioreplicate`, `techrep`, `techreplicate`
   * Examples:
     * `Rep1` -> `replicate <N>`
     * `BioRep2` -> `biorep <N>`
     * `replicate-1` / `rep_1` -> `replicate <N>`

3. Keyword-anchored replicate indices:
   * Normalize numeric suffixes only when preceded by (case-insensitive): `sample`, `animal`
   * Examples:
     * `sample 1` -> `sample <N>`
     * `animal 1` -> `animal <N>`

4. Optional: normalize trailing `#<N>` tokens at end of title (replicate-like):
   * Example: `..., #1` -> `..., #<N>`

Do not apply broad numeric normalization beyond these anchored patterns. Do not change any other lines in context_text.

This change affects only fingerprint generation for caching. Prompts, outputs, and pipeline semantics remain unchanged.

## Acceptance Criteria

1. Titles differing only by patient/donor/subject IDs or explicit replicate markers normalize to the same fingerprint when other semantic lines are identical.
2. Titles that differ in potentially semantic tokens (e.g., timepoints like T1/T2, condition labels) remain different.
3. Deterministic behavior.

## Required Tests

Add unit tests verifying:
1. `donor_001` vs `donor_002` -> same fingerprint
2. `Rep1` vs `Rep2` and `BioRep1` vs `BioRep2` -> same fingerprint
3. `PTL_patient_O23_1` vs `PTL_patient_R-27_1` -> same fingerprint
4. `Control_T1` vs `Control_T2` -> different fingerprint (guardrail)

Run:
`uv run pytest -q`
