# Ticket #72: Add config-gated terminal fallback allowlist for data_type = "Microarray" when EFO assay slice cannot match

## Problem

The ontology DB for `data_type` was built from the EFO *assay* branch only. As a result, `data_type = "Microarray"` is not present and cannot be ontology-matched, even though many GEO records deterministically imply microarray-based experiments.

This leads to unnecessary grounding failures or low-confidence statuses for a value that is intended to be allowed in outputs.

## Scope (minimal, deterministic)

Add a config-gated terminal fallback allowlist for `data_type` that includes "Microarray" (case-insensitive).

Behavior:
* If proposed `data_type` normalizes to "Microarray" and allowlist is enabled:
  * accept the value as a terminal fallback for data_type
  * set ontology status for data_type to FALLBACK (not MATCHED)
  * ensure behavior is auditable
* If allowlist is disabled:
  * current behavior remains unchanged

No changes to:
* ontology DB content
* ontology matching rules
* decision routing rules
* output schema

## Acceptance Criteria

1. When config enables the allowlist, `data_type = "Microarray"` is accepted deterministically.
2. The ontology grounding record for `data_type` reports FALLBACK (not MATCHED) for this value.
3. When config disables the allowlist, behavior is unchanged.
4. Existing RNA-Seq and other matched assay types are unaffected.

## Required Tests

Add regression tests:
1. With allowlist enabled, "Microarray" yields ontology status FALLBACK and is accepted.
2. With allowlist disabled, "Microarray" does not become accepted via this path (existing behavior).

Run:
`uv run pytest -q`

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-72.md` and paste this ticket verbatim.
