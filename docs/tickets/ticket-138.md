# Ticket #138: Add `--verbose` runtime tracing for pipeline execution steps

## Background

The GEO GSM Annotator Agent has a deterministic, multi-stage pipeline
(SOFT ingest → parsing → LLM proposal → validation → ontology grounding →
decision routing → output emission), but the CLI currently emits only minimal
runtime feedback.

For batch workflows, debugging, and long-running runs, users need a clear,
step-by-step trace of *what the agent is doing* and *where time is being spent*,
without changing behavior or polluting audit artifacts.

## Problem Statement

There is no standardized way to observe pipeline progress at runtime.
Users cannot easily tell whether the system is:
- downloading or reading SOFT files,
- parsing metadata,
- calling the LLM,
- running validation or ontology grounding,
- or writing outputs.

This makes batch runs opaque and debugging harder than necessary.

## Proposed Change

Introduce a `--verbose` CLI flag that enables structured runtime messages
for **major pipeline milestones only**, without altering semantics.

### CLI change

Add a new option: `--verbose`

Semantics:
- Disabled by default (no behavior change).
- When enabled, emit informative runtime messages for each major step.
- Messages go to stderr or the project logger (not to JSONL outputs).

### Verbose message scope (required)

When `--verbose` is enabled, emit messages at the following points:

#### Ingest / SOFT handling
- Start processing a GSE:
  - `INFO: GSE12345: start processing`
- Local SOFT resolved:
  - `INFO: GSE12345: using local SOFT`
- Remote SOFT download started:
  - `INFO: GSE12345: downloading SOFT via https`
- Remote SOFT download completed:
  - `INFO: GSE12345: SOFT downloaded`
- SOFT parsing completed:
  - `INFO: GSE12345: SOFT parsed`

#### LLM proposal
- Before LLM call:
  - `INFO: GSM1234567: calling LLM for annotation proposal`
- After LLM proposal received:
  - `INFO: GSM1234567: LLM proposal received`

(Do **not** log prompt contents or model outputs.)

#### Validation and grounding
- Validation completed:
  - `INFO: GSM1234567: validation completed`
- Ontology grounding started:
  - `INFO: GSM1234567: ontology grounding started`
- Ontology grounding completed:
  - `INFO: GSM1234567: ontology grounding completed`

#### Decision and repair
- Decision routing completed:
  - `INFO: GSM1234567: decision = ACCEPT|FLAGGED`
- Repair loop entered (if applicable):
  - `INFO: GSM1234567: entering repair loop`
- Repair loop exited:
  - `INFO: GSM1234567: repair loop completed`

#### Output
- Output written:
  - `INFO: GSE12345: outputs written to <output-dir>`

### Design constraints

- Messages must reflect **actual completed stages**, not assumptions.
- No free-text rationales.
- No duplication of audit or evidence semantics.
- No logging of sensitive data (prompts, raw LLM text, ontology internals).
- Message format should be stable and grep-friendly.

### Implementation notes

- Prefer using an existing logger if present.
- Gate all messages behind `--verbose` (no partial verbosity).
- Avoid scattering ad-hoc prints; centralize helpers where possible.
- Do not introduce logging levels beyond this flag in this ticket.

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change (policy-spec.md must be updated)

This ticket introduces **observability only**. It must not change:
- pipeline order,
- decision logic,
- repair behavior,
- outputs,
- or audit artifacts.

## Acceptance Criteria

1. `geo-gsm-annotate -h` lists `--verbose` with clear help text.
2. With `--verbose` disabled:
   - CLI output behavior matches current baseline exactly.
3. With `--verbose` enabled:
   - Messages appear for all major stages listed above.
   - Messages correctly reflect local vs remote SOFT usage.
4. No verbose messages appear in:
   - `annotations.jsonl`
   - `audit.jsonl`
   - `evidence.jsonl`
5. Batch runs (`--gse-file`) produce per-GSE and per-GSM messages without interleaving confusion.
6. All existing tests pass, and new tests (if added) do not assert on message text unless strictly necessary.
7. `uv run pytest -q` passes.

## Non-Goals

- No timing or performance metrics.
- No per-function debug logging.
- No log-level framework redesign.
- No UI changes.

## Constraints

- Deterministic behavior must be preserved.
- Messages must not imply correctness or success beyond actual decisions.
- Verbose output must be safe for long batch runs.

## Guiding Principle

**Observability without interpretation.**  
Verbose output explains *what happened*, not *why it was correct*.

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-138.md` and paste this ticket verbatim.
