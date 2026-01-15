# Ticket #62: UI-OVR-001 — Override safety via warnings, confirmation, diff, and revert (no hard blocking)

## Background

Ontology canonicalization, terminal exact matches, and field locking indicate **high confidence in the ontology step**, not absolute correctness. A value may still originate from an incorrect upstream LLM proposal and must remain correctable by a human curator.

Therefore, the UI must **never hard-block editing** of any field. Instead, it should provide **clear signals, soft warnings, and explicit confirmation** to prevent accidental overrides while fully supporting legitimate curator corrections.

This ticket refines override ergonomics inside the GSM detail modal without changing backend behavior, schemas, or persistence.

---

## Scope (STRICT)

### In scope

1. **Always-available editing**

   * When editing mode is enabled, **all fields remain editable**, including:

     * locked fields
     * canonicalized fields
     * terminal exact matches
   * No field may be disabled or made read-only solely due to backend confidence.

2. **Soft warning indicators (display-only)**
   For fields marked by backend as any of the following:

   * LOCKED
   * TERMINAL EXACT
   * CANONICALIZED

   Display a concise inline warning near the field editor, for example:

   * “Backend marked this value as terminal exact and canonicalized.”
   * “You may override this if the annotation is incorrect.”

   These warnings are informational only.

3. **Confirmation on applying override**
   When the curator attempts to apply/save an override for a field with any of the above high-confidence signals:

   * Show a confirmation dialog/modal:

     * Field name
     * Backend value
     * Proposed override value
   * Require an explicit “Confirm override” action to proceed.
   * For fields without high-confidence signals, no confirmation is required.

4. **Inline diff display**
   For any field that is overridden in the current session, display:

   * Backend value
   * Override value
   * A clear “OVERRIDDEN” indicator

   This must update dynamically as overrides are added or removed.

5. **Per-field revert**

   * Provide a “Revert” control per overridden field.
   * Revert removes the override from session state and restores backend value in the UI.

6. **No change to override export**

   * Overrides export format, schema, and semantics must remain exactly unchanged.

---

## Explicitly Out of Scope

* Backend changes of any kind
* Persistence or saving of UI state
* Learning from human edits
* Cross-GSM propagation
* Any new schema fields or audit emission changes

---

## Implementation Notes (Non-binding guidance)

* Implement small, pure helpers to determine:

  * whether a field has high-confidence backend signals
  * whether confirmation is required
  * whether a field is overridden
* Confirmation state must be UI-only and session-scoped.
* Avoid modal nesting where possible; keep confirmations concise.

---

## Acceptance Criteria

1. All fields are editable when editing mode is enabled, regardless of backend confidence.
2. Fields with LOCKED / TERMINAL / CANON signals show clear warnings but remain editable.
3. Applying an override to a high-confidence field requires explicit confirmation.
4. Overridden fields display backend vs override diff and an OVERRIDDEN indicator.
5. Revert restores backend value and clears override state.
6. No backend code changes.
7. All tests pass:

```
uv run pytest -q
```

---

## Tests Required

Add/update tests under `tests/ui/`:

1. **Edit availability**

   * Locked/canonicalized fields are editable when editing mode is enabled.

2. **Confirmation gating**

   * Override on high-confidence field requires confirmation.
   * Override on low-confidence field does not.

3. **Diff and revert**

   * Diff appears after override.
   * Revert clears override and restores backend value.

Tests must be deterministic and not require a browser session.

---

## Ticket file requirement (MANDATORY)

Replace the contents of `docs/tickets/ticket-62.md` with this ticket **verbatim**.

