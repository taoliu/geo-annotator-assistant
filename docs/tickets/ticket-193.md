# Ticket #193: Extend output statistics script with repair outcomes and ontology match-route counts

## Background

The initial ARTNet output statistics script reports total repair activity, ontology
canonicalization counts, and overall LLM usage.

After reviewing the report, two follow-up questions remain operationally important:

1. Of GSMs that entered repair activity, how many ultimately moved forward to `ACCEPT`
   versus ended `FLAGGED` after repair attempts?
2. Among ontology matches, how many were achieved through:
   - exact label / exact ID matching
   - exact synonym matching
   - semantic similarity matching that still passed the acceptance threshold

These distinctions are already present in the emitted audit artifacts, but the current
script does not summarize them explicitly.

## Problem Statement

The current reporting utility does not expose:

- repair outcome split (`repaired_then_accepted` vs `repaired_then_flagged`)
- a separate split for true LLM repair attempts
- ontology match-route counts by exact label/ID, exact synonym, and thresholded
  semantic match

Without these breakdowns, the report is less useful for understanding repair yield and
how strongly ontology grounding is relying on deterministic exact matching versus
similarity-based acceptance.

## Proposed Change

Extend the existing read-only stats script under `scripts/` so it additionally reports:

1. Repair outcome counts:
   - GSMs with any repair activity that ended `ACCEPT`
   - GSMs with any repair activity that ended `FLAGGED`
   - GSMs with at least one LLM repair attempt that ended `ACCEPT`
   - GSMs with at least one LLM repair attempt that ended `FLAGGED`
   - optionally, fallback-only and salvage-only accepted/flagged counts if present

2. Ontology matched-route counts, based on emitted `validation.ontology_matches` records:
   - exact label / exact ID matches
   - exact synonym matches
   - semantic threshold matches (`status == MATCHED` but non-exact match type)

3. Include these metrics in both:
   - text output
   - JSON output

Definitions must remain artifact-driven and deterministic:

- repair outcomes come from `repair_history` plus final decision
- ontology route counts come from `status` and `match_type` already emitted in audit

## Layer Affected

- [ ] Canonicalization
- [ ] Ontology grounding
- [ ] Validation / Repair
- [ ] Decision routing
- [ ] UI only
- [ ] Documentation only

Reporting / read-only utility only.

## Policy Impact

- [x] No policy change
- [ ] Policy clarification only
- [ ] Policy change (policy-spec.md must be updated)

This ticket changes reporting only and must not alter backend semantics or emitted
artifacts.

## Acceptance Criteria

1. The stats script reports repair outcome splits in text and JSON output.
2. The stats script reports ontology match-route counts in text and JSON output.
3. Ontology route counting uses current audit semantics for `status` and `match_type`.
4. A focused automated test covers:
   - repaired-and-accepted vs repaired-and-flagged counts
   - exact label/ID vs exact synonym vs semantic-threshold ontology route counts
5. `uv run pytest -q tests/test_artnet_output_stats.py` passes.

## Non-Goals

- Any backend behavior change.
- Any reinterpretation of ontology thresholds beyond emitted audit fields.
- Any change to output JSONL schemas.

## Constraints

- Continue to use emitted artifacts as ground truth.
- Do not re-run ontology matching or repair logic.
- Keep the script deterministic and read-only.

## Guiding Principle

The report should explain what the pipeline already did, not infer new semantics.

## Ticket File Requirement (MANDATORY)

Create `docs/tickets/ticket-193.md` and paste this ticket verbatim.
