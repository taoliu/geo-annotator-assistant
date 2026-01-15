# Ticket #61: UI-MODAL-002 — Add per-field expandable “Evidence” panel in GSM detail modal (grounding facts only)

## Background

Curators need to understand **why** a field matched, was canonicalized, or failed grounding. The current modal shows details, but grounding evidence is not presented in a compact, field-scoped, curator-friendly way.

This ticket adds an **expandable evidence panel per field** inside the GSM detail modal, using only existing audit/state produced by the backend (read-only). No new inference or backend changes are allowed.

---

## Scope (STRICT)

### In scope

1. **Evidence panel per ontology-backed field**
   For each field that has ontology grounding in the backend:

   * `data_type`
   * `tissue_type`
   * `cell_line`
   * `disease`

   Add an expandable UI section (collapsed by default) labeled:

   * “Evidence” or “Why this match?”

2. **Evidence contents (structured facts only)**
   Display only structured values already present in UI state/audit logs. When available, show:

   * raw value (pre-cleaning / original)
   * normalized value (post-cleaning)
   * selected ontology source (for example DOID vs NCIT for disease)
   * match status (MATCHED / NO_MATCH / AMBIGUOUS, etc.)
   * match_type (label / synonym / ID / normalized label, etc.)
   * score
   * canonical label used (if canonicalized)
   * locked flag (if locked)
   * “terminal exact” flag (if available)

   If a datum is not available, omit it. Do not invent placeholders beyond “(not available)”.

3. **No free-text rationale**

   * No generated explanations.
   * No “because …” prose beyond short UI labels.
   * This must remain auditable and deterministic.

4. **Layout and readability**

   * Use a compact key:value layout.
   * Collapse by default to keep the modal clean.
   * Provide a single “Expand all evidence” toggle at the top of the modal (optional but recommended).

5. **Do not change edit/override behavior**

   * Evidence panels are read-only.
   * Overrides continue to function as today.
   * Evidence display must reflect backend truth, not overridden values (except that you may show both “backend value” and “override value” if already present elsewhere).

---

## Explicitly Out of Scope

* Any backend changes (grounders, canonicalization, thresholds, retrieval)
* Any schema changes
* Any new audit emission (must reuse what already exists)
* Any persistence or learning
* Evidence for non-ontology fields (organism, treatment) unless already present in audit

---

## Implementation Notes (Non-binding guidance)

* Implement a small adapter function in `src/ui/` to extract evidence fields from the current UI record object/audit structure, for unit testing.
* Keep extraction logic defensive: missing keys must not break rendering.

---

## Acceptance Criteria

1. For each ontology-backed field, the modal shows a collapsed-by-default evidence section.
2. Evidence shows structured grounding facts (raw/normalized/status/match_type/score/source/canonical/locked) when present.
3. No free-text rationale is introduced.
4. The UI remains responsive (evidence is not rendered for all rows, only within the opened modal).
5. All tests pass:

```
uv run pytest -q
```

---

## Tests Required

Add/update tests under `tests/ui/`:

1. **Evidence extraction helper**

   * Given a mock record/audit dict, extracted evidence contains expected keys/values.

2. **Missing data robustness**

   * Evidence rendering does not crash when some evidence keys are absent.

Tests should be deterministic and not require a browser session.

---

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-61.md` and paste this ticket verbatim.

---
