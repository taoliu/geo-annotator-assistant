# Ticket #106: Show LLM Original Field Values in Modal (from audit.jsonl) and Document UI Contract

## Background

Curators can now see backend values and overridden values in the GSM detail
modal. For full context, curators also want to see the **initial LLM-proposed
values**, which are already available in `audit.jsonl` under
`llm_parsed_outputs`.

Adding these values to `curation.jsonl` would be a backend schema change and is
out of scope for v1.0. However, audit artifacts are explicitly intended to carry
auxiliary history and diagnostics.

## Problem Statement

The Curator UI does not currently expose the original LLM proposal for each
field, even when `audit.jsonl` is present. As a result, curators cannot easily
see the full trajectory:

LLM proposal → deterministic validation / repair / canonicalization → final
backend output → optional human override.

Additionally, the UI documentation (`docs/ui.md`) does not currently describe
optional consumption of `audit.jsonl`.

## Proposed Change (UI Only)

### 1. Optional audit.jsonl Loading

- Extend the UI loader to **optionally** read `audit.jsonl` from the same
  `--input-dir`.
- Build a lookup keyed by `gsm_accession` (with `gse_accession` sanity check).
- UI behavior must remain unchanged if `audit.jsonl` is absent.

### 2. LLM Original Display in GSM Modal

In the GSM detail modal, for each field:

- Add a read-only row labeled **“LLM original”**, displayed only if available.
- The value is taken from:
  `audit.llm_parsed_outputs[0][<field>]`
  (the first parsed output, representing the initial LLM proposal).
- Clearly label this as an initial proposal, not a final or validated value.

Display order (conceptual):
- Backend value
- LLM original (if present)
- Overridden value (if present)

### 3. Documentation Update (`docs/ui.md`)

Update `docs/ui.md` to document:

- `audit.jsonl` as an **optional UI input artifact**.
- What information is sourced from `audit.jsonl` (LLM original proposals).
- That `curation.jsonl` and `evidence.jsonl` remain the authoritative UI inputs.
- That audit data is read-only and does not affect backend logic or decisions.

## Why No Backend Change Is Required

- `audit.jsonl` already contains the required information.
- No JSONL schemas are modified.
- No backend logic, policy, or decision semantics are affected.

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change

## Acceptance Criteria

1. When `audit.jsonl` is present, the GSM modal shows “LLM original” values
   sourced from `llm_parsed_outputs[0]`.
2. When `audit.jsonl` is absent, the UI behaves exactly as before.
3. “LLM original” values are clearly labeled and visually distinct from backend
   and overridden values.
4. No JSONL files are modified or written.
5. `docs/ui.md` accurately documents optional `audit.jsonl` support.

## Non-Goals

- No attempt to reconstruct LLM originals if missing.
- No replacement of `curation.jsonl` or `evidence.jsonl` as required inputs.
- No backend schema consolidation.

## Constraints

- Read-only use of audit artifacts.
- Do not block initial GSM table rendering on audit loading.
- Preserve determinism and auditability.

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-106.md` and paste this ticket verbatim.
