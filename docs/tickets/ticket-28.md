# Ticket #28: Anti-cycling repair constraint for terminal fallback fields

### Problem

After recent fixes, the repair loop converges correctly for most real-world GSMs. However, there is still a conceptual gap:

Once a field has been **fallbacked to a terminal value**, the repair loop may later attempt to **repair the same field again** in the same run, if downstream validation reintroduces a failure signal.

Examples of terminal fallback values currently in use:

* `disease → "Unknown"`
* `tissue_type → "Unknown"`
* `cell_line → "No"` / `"Unknown"`
* `treatment → "None"`

While field-scoped REPAIR updates fixed most oscillations, the system still lacks an explicit **anti-cycling constraint** that treats these fallback values as *terminal decisions* for the remainder of the run.

### Goal

Introduce an explicit anti-cycling rule:

> Once a field has been fallbacked to a terminal value in a given run, **do not repair or fallback that field again** in the same run.

This should:

* Prevent unnecessary LLM calls
* Prevent wasted repair attempts
* Reduce risk of `max_repairs_exceeded`
* Preserve deterministic convergence behavior

### Scope

**In scope**

* Track terminal fallback events at runtime
* Prevent subsequent REPAIR actions on those fields
* Clear failures for terminal fields and revalidate
* Minimal, local change to repair loop logic

**Out of scope**

* Redesign of decision engine
* Changes to validators or ontology logic
* Cross-run persistence of terminal states

### Proposed Design

1. Extend `PipelineState` with:

   ```python
   terminal_fallback_fields: set[str]
   ```

2. Define terminal fallback values per field (initial set):

   ```python
   {
     "disease": {"Unknown"},
     "tissue_type": {"Unknown"},
     "cell_line": {"No", "Unknown"},
     "organism": {"Unknown"},
     "data_type": {"Unknown"},
     "treatment": {"None"},
   }
   ```

3. In `apply_repairs()`:

   * When a FALLBACK sets a terminal value, record the field in `terminal_fallback_fields`
   * Before executing a REPAIR decision:

     * If `field in terminal_fallback_fields`, skip REPAIR
     * Clear failures for that field
     * Re-run validation
     * Continue loop

### Acceptance Criteria

* A field fallbacked to a terminal value is not repaired again in the same run
* Repair attempts for terminal fields do not increase `attempts_by_field`
* No regression in existing unit tests
* Real-world GSMs that previously converged continue to converge
* Previously flagged GSMs do not regress to `max_repairs_exceeded` due to cycling

### Suggested Tests

* Unit test: terminal fallback blocks subsequent REPAIR for same field
* Integration test: GSM with disease fallback does not attempt further disease repair
* Ensure `attempts_by_field` remains stable after terminal fallback

### Notes

This ticket formalizes behavior that is already implicitly expected by the decision table and fallback semantics. Making it explicit improves robustness, clarity, and performance without changing system architecture.

---

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-28.md` and paste this ticket verbatim.
