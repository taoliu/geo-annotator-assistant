# Ticket #65: Clarify output artifact roles and canonical schema in documentation

## Problem

The pipeline produces multiple output artifacts (`annotations.jsonl`, `audit.jsonl`, `curation.jsonl`, etc.), but the documentation does not clearly state:

* which artifact is the canonical final output governed by the 8-field invariant
* which artifacts are diagnostic or UI-facing only
* which invariants apply to which files

This ambiguity can lead to incorrect assumptions about schema violations or backend behavior by developers and AI assistants.

## Scope (documentation only)

Update documentation to explicitly define the role of each output artifact produced by a GSE run.

No code changes.  
No backend behavior changes.  
No schema changes.

## Required Changes

Update `README.md` to include a section describing output artifacts, with at least the following clarifications:

* **`annotations.jsonl`**
  * Canonical final output
  * Exactly 8 fields per GSM:
    * `gse_accession`
    * `gsm_accession`
    * `data_type`
    * `organism`
    * `tissue_type`
    * `cell_line`
    * `disease`
    * `treatment`
  * Governed by the whitepaper’s output contract

* **`audit.jsonl`**
  * Authoritative diagnostics and execution trace
  * Validation, ontology grounding, repair history, decision routing
  * Not schema-restricted

* **`curation.jsonl` / `curation.tsv`**
  * UI-facing, non-canonical, derived artifacts
  * May include decisions, flags, ontology status summaries
  * Must not be treated as schema-governed final output

* **`flagged.jsonl`**
  * Subset view of GSMs requiring curator attention
  * Derived, non-authoritative

* **`evidence.jsonl`**
  * Structured evidence snapshots for UI and review
  * Read-only, diagnostic

* **`gse_consistency.json`**
  * Advisory cross-GSM diagnostics
  * Must not influence GSM-level decisions

## Acceptance Criteria

1. `README.md` clearly identifies `annotations.jsonl` as the canonical final output.
2. Documentation explicitly states that UI-facing artifacts are non-canonical.
3. No change to backend code, pipeline behavior, or output generation logic.

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-65.md` and paste this ticket verbatim.
