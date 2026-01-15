# Ticket #60: UI-MODAL-001 — Add “Field Status Dashboard” at top of GSM detail modal (8 fields + badges)

## Background

The GSM detail modal currently shows detailed record content, but curators still need to scan through sections to understand what requires attention.

We need a compact “at-a-glance” dashboard at the top of the modal summarizing the status of each of the **8 output fields**, using only backend-produced truth and existing UI override state.

This is UI-only and must not change backend behavior.

---

## Scope (STRICT)

### In scope

1. **Add a top-of-modal dashboard**
   Display the 8 fields in a compact grid (2×4 or 4×2), one card/pill per field:

   * `data_type`
   * `organism`
   * `tissue_type`
   * `cell_line`
   * `disease`
   * `treatment`
   * plus identifiers shown separately:

     * `gse_accession`
     * `gsm_accession`

   Each field item must show:

   * field name
   * current displayed value (backend value unless overridden in session)
   * one or more status badges

2. **Status badges (display-only)**
   Badges must be derived from existing data already available to the UI (audit/state), and must not trigger any backend recomputation.

   Minimum badge set:

   * **LOCKED** — field locked by backend (terminal exact lock)
   * **CANON** — field value was canonicalized by backend
   * **TERM** — terminal exact match (if available separately from locked)
   * **AMBIG** — ambiguous / low confidence grounding (if available)
   * **NO-MATCH** — ontology grounding failed (if available)
   * **OVERRIDDEN** — field changed in current session

   If some of these signals are not currently available in the UI state, display only what is available and leave others out (do not invent new signals).

3. **Consistent value precedence**
   Displayed value precedence must be:

   1. session override (if present)
   2. backend final output value

   This is display-only and must match existing override semantics.

4. **Clickable jump links (optional but recommended)**
   Clicking a field item in the dashboard scrolls/jumps to that field’s section in the modal (or expands that field panel if the modal is structured that way).

   This must be UI-only and best-effort.

---

## Explicitly Out of Scope

* Any backend changes
* Any new inference, validation, grounding, repair, or RAG behavior
* Any new schema or new emitted artifacts
* Any change to override export format
* Redesign of the evidence panel (handled in next ticket)

---

## Implementation Notes (Non-binding guidance)

* Implement a pure helper that maps available per-field diagnostics to badge strings, for unit testing.
* If audit information is nested, add a thin UI adapter to extract:

  * locked status
  * canonicalized flag
  * match status/score/type categories (only if already present)

Do not add new backend-derived fields. Only consume what is already produced.

---

## Acceptance Criteria

1. The GSM detail modal shows a compact dashboard summarizing all 8 fields.
2. Badges are correct and derived only from existing UI/audit state.
3. OVERRIDDEN badge appears when a session override exists for that field.
4. No backend code changes.
5. All tests pass:

```
uv run pytest -q
```

---

## Tests Required

Add/update tests under `tests/ui/`:

1. **Badge mapping helper**

   * Given a mock per-field diagnostic structure, the helper outputs expected badges.

2. **Override precedence**

   * When override exists, dashboard displays override value and includes OVERRIDDEN badge.

Tests must be deterministic and not require a browser session.

---
