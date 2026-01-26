# Ticket #75: Add deterministic GEO context fingerprint normalizer for safe in-run caching

## Problem

Many GSMs within a GSE are replicate-like and differ only by identifier fields (e.g., Sample ID, numeric suffixes in Sample Title).
A strict “full prompt hash” cache yields low hit rates because these identifier differences change the prompt text.

We need a deterministic, conservative context fingerprint that ignores purely identifier-like noise for caching purposes.

## Scope (minimal, deterministic)

Implement a function that computes a `context_fingerprint` from `context_text` by applying only conservative normalization rules:

1. Remove the line starting with `Sample ID:` (contains GSM accession).
2. Normalize numeric-only suffixes in `Sample Title:` (e.g., `patient_01`, `patient_02`) to a placeholder form (e.g., `patient_<N>`), while preserving the rest of the title text.
3. Do not alter other lines.

Return a stable hash (e.g., sha256) of the normalized text for use as a cache key component.

No changes to pipeline semantics, outputs, or prompts.

## Acceptance Criteria

1. Two context_text blocks that differ only by Sample ID and Sample Title numeric suffix produce the same fingerprint.
2. Two context_text blocks that differ in semantic evidence lines (e.g., disease state) produce different fingerprints.
3. Behavior is deterministic.

## Required Tests

Add unit tests covering:
* same-semantic replicate pair -> same fingerprint
* different disease state -> different fingerprint

Run:
`uv run pytest -q`
