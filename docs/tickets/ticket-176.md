# Ticket #176: Composite tissue_type resolution with all-components-required matching (canonical joined output)

## Background

Real-world GSMs contain composite tissue_type strings such as:
- "Colon & Rectum"
- "bone marrow and spleen"

Example case:
- GSE184398 / GSM5585963
  - tissue_type = "Colon & Rectum"
  - current pipeline yields LOW_CONFIDENCE with alternates biased toward "colon"
  - repair loop consumed 2 attempts and did not resolve
  - final_decision FLAGGED with primary_failure = ontology_low_confidence_tissue_type

This indicates a systematic gap: composite tissue strings should be interpreted as multiple tissues that must each be ontology-grounded.

Scope: tissue_type only.

## Problem Statement

The current tissue_type ontology grounding treats the input as a single term, so composite strings:
1) often fail or become LOW_CONFIDENCE,
2) trigger unnecessary ontology-guided repair LLM calls,
3) cannot represent the correct semantics: multiple anatomical sources.

We need deterministic composite handling that:
- preserves determinism,
- avoids schema changes,
- requires that all components match to be considered correct,
- emits canonical output consistent with current ontology canonicalization behavior.

## Proposed Change

### A. Trigger condition (tissue_type only)

1. Attempt full-string ontology grounding as today.
2. If full-string grounding is `MATCHED` via terminal exact match, do NOT split.
3. If full-string grounding is not terminal exact (e.g., `LOW_CONFIDENCE`), attempt composite detection + resolution.

### B. Composite splitting (deterministic)

Split raw tissue_type only when condition A.3 holds, using separators:
- `&`, `/`, `,`, `;`, and word-boundary `and`

Rules:
- normalize whitespace around separators,
- preserve original fragment order,
- drop empty fragments.

### C. Per-fragment ontology grounding

For each fragment, run the existing tissue_type (Uberon) ontology grounding pipeline.

Let:
- `k` = number of fragments
- `m` = number of fragments that reach `MATCHED` by terminal exact match

### D. All-components-required semantics

1) If `m == k` (all fragments matched):
- set `ontology_status_tissue_type = MATCHED`
- set final `tissue_type` to the canonical labels joined by `" & "` in fragment order
  - example: `"colon & rectum"`
- do NOT emit `ontology_low_confidence_tissue_type`
- do NOT enter the ontology-guided repair loop for tissue_type
- decision routing: tissue_type contributes no failure

2) If `0 < m < k` (partial match):
- set `ontology_status_tissue_type = LOW_CONFIDENCE`
- set `final_decision = FLAGGED`
- set `primary_failure = ontology_partial_composite_tissue_type`
- emit flag: `ontology_partial_composite_tissue_type`
- do NOT enter the ontology-guided repair loop for tissue_type

3) If `m == 0`:
- preserve existing behavior (likely `ontology_low_confidence_tissue_type` with existing repair loop behavior)

### E. Repair loop short-circuit

Composite resolution must happen before ontology-guided repair, and for cases D.1 and D.2 it must short-circuit the repair loop to prevent wasting LLM calls.

### F. Audit clarity (audit.jsonl only)

Add an audit-only structure describing composite handling for tissue_type, e.g.:

- raw_value
- fragments (post-split)
- per-fragment match summary (term_id, label, confidence/status)
- selection_rule = "all_components_required_v1"
- final_joined_label (when D.1 applies)

No schema change to curation.jsonl or evidence.jsonl is required.

## Policy Impact

[x] Policy change required.

Update `docs/policies/policy-spec.md`:
- Add a dedicated subsection under tissue_type describing composite handling:
  - trigger condition
  - splitting rules
  - all-components-required semantics
  - canonical joined output rule (`" & "`)
  - new failure code and flag: `ontology_partial_composite_tissue_type`
  - repair-loop short-circuit requirement

No change to `docs/whitepaper.md` is expected.

## Acceptance Criteria

1) GSM5585963 (GSE184398):
- If both "Colon" and "Rectum" are ontology-grounded via terminal exact match,
  final_output.tissue_type is `"colon & rectum"`,
  ontology_status_tissue_type is `MATCHED`,
  no repair attempts are consumed for tissue_type,
  final_decision is not FLAGGED due to tissue_type.

2) Partial composite case:
- For a composite tissue_type where only some fragments match,
  the run is deterministically FLAGGED with:
  - primary_failure = `ontology_partial_composite_tissue_type`
  - evidence flag includes `ontology_partial_composite_tissue_type`
  - ontology_status_tissue_type = `LOW_CONFIDENCE`
  - no repair attempts are consumed for tissue_type.

3) Non-composite guard:
- A known single anatomical concept containing "and" that is terminal-exact matched as a full string must not be split (regression test).

Regression case: "head and neck" must:
 * resolve via full-string synonym match
 * not trigger composite splitting
 * canonicalize to the Uberon preferred label
 * consume zero repair attempts

4) Determinism:
- Multiple reruns produce identical audit/evidence/curation outputs.

## Non-Goals

- No schema change to represent multi-valued tissue_type externally.
- No UI redesign beyond showing whatever backend flags/statuses already output.
- No new LLM calls.

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-176.md` and paste this ticket verbatim.
