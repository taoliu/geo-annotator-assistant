# Ticket #179: Add `validation.format_error_details` for format errors (field attribution, no behavior change)

## Background

We observed runs flagged with:

- validation.format_errors = ["word_limit_violation"]
- final_decision = FLAGGED
- flags = ["format_unrepaired"]
- primary_failure = "word_limit_violation"

Example: GSE227108 / GSM7091755 had spaced accessions in LLM output
("GSE2 7 1 0 8", "GSM7 0 9 1 7 5") which exceed default per-field limit=5
and trigger `word_limit_violation`.

Currently, audit.jsonl shows only the record-level format error code and does not
explain which fields triggered it, what limits were applied, or the observed counts.

Codex confirmed:
- `word_limit_violation` is computed per-field (whitespace word count),
  but recorded as record-level `format_errors`.
- All REQUIRED_KEYS are checked, including accessions.
- Field attribution is computed internally but not persisted to audit/evidence.

## Problem Statement

Format errors lack structured attribution in audit output.
This blocks deterministic debugging and policy refinement because we cannot tell
which field(s) triggered `word_limit_violation` or what limit was used.

We need audit-level transparency without changing any decision semantics.

## Proposed Change (Observability only, no behavior change)

Add an optional structured list to audit.jsonl under `validation`:

- `format_error_details: list[FormatErrorDetail]`

Where each item includes:

- `code`: format error code string (e.g., "word_limit_violation")
- `field`: field name that triggered the error (e.g., "gse_accession")
- `limit_used`: integer limit used for that field
- `observed_word_count`: integer word count observed (whitespace split, consistent with validator)
- `stage`: one of:
  - "initial" (first validation pass)
  - "format_repair" (format repair attempts)
  - "repair_loop" (field repair loop validation)

Requirements:
- Deterministic ordering:
  - order by `code` then by `field` in REQUIRED_KEYS order
- Keep existing `validation.format_errors` unchanged.
- Keep all existing decisions/flags unchanged.
- No schema change to curation.jsonl or evidence.jsonl.

Implementation note (non-normative):
- Reuse existing internal attribution helper (e.g., `_format_error_fields`) or compute
  details directly where `validate_format(...)` evaluates per-field limits.

## Policy Impact

[x] Policy change required (documentation only).

Update policy-spec.md to specify:
- format errors are record-level for decision routing
- audit must include per-field attribution via `validation.format_error_details`

No change to whitepaper is expected.

## Acceptance Criteria

1) Repro case (spaced accessions) includes `format_error_details` entries for:
   - gse_accession and/or gsm_accession
   - code = "word_limit_violation"
   - limit_used = 5 (default)
   - observed_word_count reflects whitespace split (e.g., 8 or 9)
   - stage = "initial"

2) No behavior change:
   - primary_failure, format_errors list, final_decision, flags remain identical.

3) Determinism:
   - repeated runs produce identical `format_error_details` ordering and values.

## Non-Goals

- No change to format validation logic.
- No change to repair behavior.
- No UI changes (UI may optionally consume these details later).

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-179.md` and paste this ticket verbatim.
