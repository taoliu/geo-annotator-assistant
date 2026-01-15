# Ticket #63: UI-TABLE-001 — Table-level ergonomics: filters, summary counts, and quick triage

## Background

With modal-based GSM inspection in place, the curation table should support **fast triage** across many GSMs. Curators need to quickly identify which records require attention, which are clean, and which already have overrides, without opening each modal.

This ticket adds **table-level ergonomics** only. No backend logic or semantics may change.

---

## Scope (STRICT)

### In scope

1. **Summary strip above the table**
   Add a compact summary bar above the curation table showing counts derived from UI state:

   * Total GSMs
   * GSMs needing attention (any field ambiguous / no-match)
   * GSMs with overrides (session-only)
   * GSMs fully clean (all fields terminal exact / canonicalized, if signals exist)

   Counts must be computed from existing UI/audit state only.

2. **Quick filters (UI-only)**
   Add simple toggle filters that affect **table display only**:

   * **Needs attention**

     * Show GSMs where at least one field is ambiguous, low confidence, or no-match (based on available signals).
   * **Has overrides**

     * Show GSMs with any session override.
   * **Clean**

     * Show GSMs with no ambiguous/no-match fields and no overrides.
   * **All**

     * Default view.

   Filters must be mutually exclusive or clearly composable (pick one approach and document it in UI text).

3. **Non-destructive filtering**

   * Filtering must not:

     * alter session override state
     * affect export
     * affect backend truth
   * Clearing filters must restore the full table.

4. **Visual cues in table rows**
   Add subtle row-level indicators (icons or color accents) to reinforce filter logic:

   * “Needs attention” indicator
   * “Overridden” indicator

   These cues must match the same logic used by filters and summary counts.

---

## Explicitly Out of Scope

* Backend changes of any kind
* New audit signals
* New schema fields
* Persistence of filter state across sessions
* Sorting by confidence or score (filtering only)

---

## Implementation Notes (Non-binding guidance)

* Implement pure helper functions in `src/ui/` to compute per-GSM flags:

  * `needs_attention(gsm)`
  * `has_overrides(gsm)`
  * `is_clean(gsm)`
* Use these helpers consistently for:

  * summary counts
  * filter predicates
  * row indicators
* Default filter state should be **All**.

---

## Acceptance Criteria

1. Summary strip displays correct counts and updates dynamically with overrides.
2. Filters change only the table view and can be cleared.
3. Row indicators align with filter logic.
4. No backend or export behavior changes.
5. All tests pass:

```
uv run pytest -q
```

---

## Tests Required

Add/update tests under `tests/ui/`:

1. **Helper logic**

   * Given mock GSM UI records, helpers correctly classify:

     * needs attention
     * has overrides
     * clean

2. **Filter application**

   * Applying a filter reduces table rows deterministically.
   * Clearing filter restores full set.

Tests must be deterministic and not require a browser session.

---

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-63.md` and paste this ticket verbatim.

---
