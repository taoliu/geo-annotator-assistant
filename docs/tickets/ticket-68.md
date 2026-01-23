# Ticket #68: Make NCIT synonym exact matching produce terminal exact (score 1.0) and prefer terminal exact across sources

## Problem

For disease value “B cell malignancies”, audit shows:

* NCIT fallback is triggered (`ncit_triggered: true`, `attempted_sources` includes NCIT)
* but the selected source remains DOID with `status: LOW_CONFIDENCE` and `score: 0.5`
* selection rule indicates a tie-break (`score_tie_prefer_doid`)

NCIT contains an appropriate concept (“B-Cell Malignant Neoplasm”) with synonym “B-Cell Malignancy”.
This should be detected as a deterministic exact/synonym match (terminal exact) after normalization and simple morphological handling.

Current behavior suggests NCIT candidates are either not found as exact/synonym matches, scored too low, or not surfaced into alternates for selection.

## Scope (minimal, deterministic)

1. Ensure NCIT disease matching applies the same normalization and simple singular/plural handling to:
   * the query string, and
   * NCIT labels and synonyms
so that synonym/label exact matches are detected and scored as terminal exact (score 1.0).

2. Update cross-source selection to always prefer a terminal exact match (score 1.0 with exact match type) over any non-terminal fuzzy match, regardless of source preference rules.
The existing “prefer DOID on tie” rule remains for genuine ties between non-terminal matches.

No changes to:
* thresholds for LOW_CONFIDENCE vs MATCHED beyond terminal-exact detection
* decision routing
* schema
* repair logic

## Acceptance Criteria

1. For “B cell malignancies”, the ontology grounding step produces an NCIT candidate via synonym/label exact with score 1.0 (terminal exact).
2. The selected source becomes NCIT when it is the only terminal exact option.
3. Audit alternates include the NCIT matched term when attempted.
4. Determinism is preserved.

## Required Tests

Add a regression test for disease grounding:
* input: “B cell malignancies”
* assert NCIT produces a terminal exact match (score 1.0, exact match type)
* assert selected_source is “NCI Thesaurus” when DOID only yields non-terminal fuzzy matches

Run:
`uv run pytest -q`

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-68.md` and paste this ticket verbatim.
