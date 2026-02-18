# Ticket #180: Override gse_accession and gsm_accession before format validation

## Background

Current behavior (confirmed by code review):

- `validate_format(...)` runs before accession override.
- `word_limit_violation` is computed per-field using whitespace word count.
- All REQUIRED_KEYS are checked, including:
  - gse_accession
  - gsm_accession
- Default word limit for unspecified fields is 5.
- LLM occasionally outputs spaced accessions like:
  - "GSE2 7 1 0 8"
  - "GSM7 0 9 1 7 5"
- These exceed word limit and trigger `word_limit_violation`.
- Later in the pipeline, accessions are overwritten with true context values.

This causes false FLAGGED runs due to format errors on fields that are explicitly non-authoritative.

We previously decided that:
- gse_accession and gsm_accession must be copied from the record context.
- LLM predictions for these fields must be ignored.

## Problem Statement

Format validation is currently applied to LLM-predicted accessions before they are overridden.
This contradicts the design invariant that accessions are non-authoritative and must be copied
from the true input context.

Result:
- False `word_limit_violation`
- Unnecessary format repairs
- Unnecessary FLAGGED decisions
- Extra LLM calls

## Proposed Change

Move accession override to occur **before any validation**.

### New Execution Order

After parsing LLM output into structured object:

1. Immediately set:
   - parsed.gse_accession := true gse_accession (from record context)
   - parsed.gsm_accession := true gsm_accession (from record context)

2. Only then run:
   - validate_format(...)
   - semantic validation
   - ontology grounding
   - repair loop

Under this change:
- Format validation will never see LLM-predicted accession values.
- Accessions will always be valid canonical strings.
- `word_limit_violation` cannot be triggered by accession fields.

## Important Constraints

- Do NOT silently drop accession fields.
- Do NOT remove accession keys from REQUIRED_KEYS.
- Accessions must remain present in parsed output.
- Determinism must remain unchanged.
- No changes to word limit behavior for other fields.

## Policy Impact

[x] Policy change required.

Update policy-spec.md to explicitly state:

- gse_accession and gsm_accession are copied from the input record context immediately after parsing.
- LLM-predicted accession values are ignored for all downstream validation and decision logic.
- Format validation must not consider LLM-predicted accession values.

This clarifies the architectural invariant and prevents silent semantic drift.

No whitepaper change required.

## Acceptance Criteria

1) For GSE227108 / GSM7091755:
   - No `word_limit_violation` triggered due to spaced accession output.
   - `validation.format_errors` does not include accession-related violations.
   - `final_decision` is not FLAGGED due to format_unrepaired (assuming no other issues).

2) Determinism:
   - Multiple reruns produce identical audit outputs.

3) Regression:
   - Other format violations (e.g., excessive disease word count) still trigger correctly.
   - Accessions in final_output always match record context values.
   - No repair attempts consumed for accession formatting.

4) Audit integrity:
   - audit.jsonl shows correct accession values consistently.
   - No discrepancy between parsed and final output accessions.

## Non-Goals

- No change to word-limit thresholds.
- No removal of format validation logic.
- No UI changes.

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-180.md` and paste this ticket verbatim.
