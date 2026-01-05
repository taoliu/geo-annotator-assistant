# Ticket #20-c: AGENT-WS-020c — Enforce synonym_exact to produce MATCHED in ontology grounding (selection override)

You are working in repo `geo-gsm-annotator-agent`.

## Context

Chroma retrieval returns ontology metadata containing `synonyms`, confirmed by direct query (DOID:1040 includes synonym `"CLL"`). However, in pipeline audits the disease field still shows:

* `status: LOW_CONFIDENCE`
* `match_type: jaccard`
* `matched_via: null`
* `matched_synonym: null`

This indicates synonym-aware matching is not being applied at the final selection step, even when an exact synonym exists.

## Goal

When `normalize(raw_value)` exactly matches `normalize(synonym)` for any retrieved candidate:

* set `status="MATCHED"`
* set `match_type="synonym_exact"`
* set `matched_via="synonym"`
* set `matched_synonym=<the matching synonym>`
* set `matched_term_id/label/source` accordingly
* set `score=1.0`

This must override any LOW_CONFIDENCE outcome.

## Non-goals

* Do not rebuild Chroma DB.
* Do not add fuzzy synonym matching.
* Do not change decision table policies.
* Do not change retrieval behavior.

## Tasks

1. Locate the final match selection logic (likely `src/validator/ontology_match.py`).
2. Ensure candidate objects reaching the matcher carry synonyms (list[str]).
3. In the selection logic:

   * check label_exact first,
   * then synonym_exact,
   * and if found, return MATCHED immediately (no threshold gating).
4. Add a regression test simulating the real structure:

   * raw = "CLL"
   * candidate label = "chronic lymphocytic leukemia"
   * candidate synonyms include "CLL"
   * Expected MATCHED with synonym_exact and score 1.0.
5. Run `uv run pytest -q`.

## Acceptance criteria

* Pipeline disease "CLL" matches DOID:1040 as synonym_exact.
* `ontology_matches.disease.status` becomes MATCHED, not LOW_CONFIDENCE.
* Audit includes `matched_via="synonym"` and `matched_synonym="CLL"`.

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-21.md` and paste this ticket verbatim.

---
