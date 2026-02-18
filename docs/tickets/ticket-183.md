# Ticket #183: Scope `organism_context_conflict` to structured sample organism context (do not scan full context_text)

## Background

False FLAGGED case:

- GSE195964 / GSM5857051
- LLM organism: "Homo sapiens"
- GEO sample organism is Homo sapiens
- audit includes:
  - consistency_flags = ["organism_context_conflict"]
  - final_decision = FLAGGED
  - primary_failure = organism_context_conflict

Codex investigation found current trigger logic:

- `consistency_validate(...)` checks predicted organism against the entire `context_text.lower()`
- If predicted contains one species name and context_text contains the other (substring match),
  it emits `organism_context_conflict`.

In this GSM, context_text includes both:
- Sample Organism: Homo sapiens
- unrelated mouse mentions in platform/protocol text (e.g., “Mus musculus”)

Therefore the rule false-triggers due to mixed text contamination.

## Problem Statement

`organism_context_conflict` currently uses broad substring scanning of free-text context
instead of a structured, sample-scoped organism context. This creates false conflicts for:

- mixed-organism series
- protocols that mention other organisms
- platforms whose descriptions include unrelated organism text

Because decision_table escalates this flag, it produces incorrect FLAGGED decisions.

## Proposed Change

Modify the consistency check so `organism_context_conflict` is computed ONLY from
structured sample organism context, not from full free-text context.

### New rule

Let:

- `org_pred` = parsed_output["organism"] (normalized)
- `org_ctx` = structured sample organism from the ingested context object
  (e.g., the explicit "Sample Organism" field), normalized

Emit `organism_context_conflict` ONLY if:
- `org_ctx` is present and non-empty, AND
- `org_pred` and `org_ctx` are different organisms (normalized exact or synonym match rules)

Important:
- Do NOT search for organism tokens in arbitrary context_text.
- Only use the structured sample organism field.

### Data source for org_ctx

Use the structured sample-level organism field already present in the context JSONL
produced by ingestion (the same value that prints as "Sample Organism: ...").
Do not derive org_ctx from protocol/platform/series free text.

### Determinism

- Normalization must be deterministic (casefold, whitespace normalize).
- If org_ctx is missing, do not emit organism_context_conflict.

## Decision Semantics

No change to decision table severity in this ticket.

- `organism_context_conflict` remains ESCALATE when it is a true conflict.
- This ticket only fixes the trigger condition to reduce false positives.

## Policy Impact

[x] Policy update required.

Update policy-spec.md to specify:

- organism_context_conflict is computed from structured sample organism context only
- free-text context mentions must not trigger organism conflicts
- mixed-organism series are allowed as long as sample organism is consistent

No whitepaper change required.

## Acceptance Criteria

1) GSM5857051 (GSE195964):
- No `organism_context_conflict` is emitted when sample organism context is Homo sapiens
  and predicted organism is Homo sapiens.
- final_decision is not FLAGGED due to organism_context_conflict.

2) True conflict case:
- If sample organism context is Mus musculus and predicted organism is Homo sapiens (or vice versa),
  `organism_context_conflict` is still emitted and escalates as before.

3) Determinism preserved across reruns.

4) No regressions to other consistency flags.

## Non-Goals

- No changes to decision_table.yaml severities.
- No changes to ingestion pipeline or schema.
- No UI changes.

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-183.md` and paste this ticket verbatim.
