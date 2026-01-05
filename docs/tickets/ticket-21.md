# Ticket #21: AGENT-WS-021 — Deterministic tie-break for synonym_exact ties (avoid ontology_ambiguous_disease)

You are working in repo `geo-gsm-annotator-agent`.

## Context

After Ticket #20 + #20b + #20c, ontology grounding can now detect `synonym_exact`. However, in real data we can have multiple ontology terms sharing the same abbreviation synonym (example: disease raw value `CLL`):

* DOID:1040 `chronic lymphocytic leukemia` has synonym `CLL`
* DOID:1036 `chronic leukemia` also has synonym `CLL`

Current thresholds:

* `min_confidence_to_accept = 0.80`
* `max_delta_for_ambiguity = 0.05`

Because both candidates score 1.0 under `synonym_exact`, the ambiguity rule fires and produces:

* `status: AMBIGUOUS`
* `ontology_ambiguous_disease`
* `matched_term_id: null`

We need a deterministic tie-break rule so exact synonym ties can still produce a single `MATCHED` result.

## Goal

When multiple candidates have `confidence == 1.0` from `synonym_exact` (or `label_exact`), apply deterministic tie-breaking to select a single best term and return `status="MATCHED"` rather than `AMBIGUOUS`, without changing thresholds.

## Non-goals

* Do not loosen thresholds globally.
* Do not add LLM calls or context-based disambiguation in this ticket.
* Do not add fuzzy matching.
* Do not rebuild ChromaDB.

---

## Design

### Tie-break rule for exact matches

If the top confidence is 1.0 and the best match_type is `label_exact` or `synonym_exact`:

1. Gather all candidates with:

   * `confidence == 1.0`
   * and `match_rank` equal to the best `match_rank` (label_exact rank 0, synonym_exact rank 1)

2. If there is more than one:

   * Prefer the candidate with the **more specific label**, approximated deterministically by:

     * larger token count of the label (after normalization), then
     * longer character length of the label, then
     * stable original order (idx)

3. After tie-break selects a single winner:

   * return `status="MATCHED"` (do not mark AMBIGUOUS for this exact-tie case)

Rationale: when multiple terms share the same abbreviation, the more specific label is usually the correct grounding for annotation, and this avoids unnecessary repair/escalation.

---

## Tasks

### 1) Implement deterministic tie-break in ontology_match

File (likely):

* `src/validator/ontology_match.py`

Update `choose_best_ontology_candidate(...)`:

* After computing `scored` but before final `status` computation:

  * detect the exact-tie situation described above
  * apply the tie-break rule and reorder/select the best candidate deterministically
  * ensure the ambiguity check does not downgrade exact-tie winners to `AMBIGUOUS`

Notes:

* Keep existing `match_rank` ordering: label_exact (best) before synonym_exact.
* Only apply this tie-break when `best_confidence == 1.0` and `best_match_type in {"label_exact","synonym_exact"}`.

### 2) Add regression unit test

Add a unit test (new or extend existing) that simulates the real ambiguity:

* raw_value: `"CLL"`
* thresholds: min_accept=0.80, max_delta=0.05
* candidates include:

  * DOID:1040 label `"chronic lymphocytic leukemia"` synonyms `["CLL"]`
  * DOID:1036 label `"chronic leukemia"` synonyms `["CLL"]`
* Expected:

  * `status == "MATCHED"`
  * `match_type == "synonym_exact"`
  * `best.term_id == "DOID:1040"` (wins by more specific label)
  * `confidence == 1.0`

Also ensure stable behavior when labels have equal length (tie falls back to idx).

### 3) Run tests

* `uv run pytest -q`

---

## Acceptance criteria

* For disease raw value `"CLL"`, ontology grounding produces:

  * `status: MATCHED`
  * `match_type: synonym_exact`
  * `matched_term_id: DOID:1040`
  * `confidence/score: 1.0`
* No `ontology_ambiguous_disease` is produced for this exact-tie case under current thresholds.
* `uv run pytest -q` passes.

---

## Ticket file requirement (MANDATORY)

Create:

* `docs/tickets/ticket-21.md`

and copy the full contents of this ticket verbatim into that file.
