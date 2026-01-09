# Ticket #54: ONTO-CANON-001 — Canonicalize terminal exact ontology matches to formal label and lock fields during repair

## Background

Today the pipeline can ground a value to an ontology term with an exact match (score 1.0), but the **final output** may still keep the model’s raw label variant (for example `Myccap`) even though the ontology label is `Myc-CaP`. This causes unnecessary variation and can trigger avoidable repair churn.

We want a deterministic, auditable improvement:

1. **Canonicalize** field values to the ontology’s formal `matched_label` when the ontology match is **terminal exact**.
2. **Lock** those fields so later repair steps cannot overwrite them.

Ontology IDs remain excluded from the final output (labels only).  

---

## Definitions (MANDATORY)

Reuse the same predicate as Ticket #53:

```python
TERMINAL_EXACT_TYPES = {"label_exact", "label_norm_exact", "synonym_exact", "term_id_exact"}

def is_terminal_exact(status: str, score: float, match_type: str) -> bool:
    return status == "MATCHED" and score == 1.0 and match_type in TERMINAL_EXACT_TYPES
```

---

## Scope (STRICT)

### In scope

1. **Config-gated behavior**
   Add two config flags (default false):

   * `rag.ontology.canonicalize_terminal_exact_labels: bool` (default false)
   * `rag.ontology.lock_terminal_exact_fields: bool` (default false)

2. **Canonicalization step (deterministic)**
   When a field has a selected ontology match where `is_terminal_exact(...)` is true, and canonicalization flag is enabled:

   * Replace `output[field]` with `matched_label` exactly as stored in ontology metadata.
   * Do not alter other fields.
   * Canonicalization must happen **after parsing** and **after ontology grounding** produces the chosen match, but **before** repair attempts for that field.

3. **Field locking (repair guard)**
   When `is_terminal_exact(...)` is true and locking flag is enabled:

   * Add a lock record to pipeline state, for example:

     * `locked_fields[field] = {"term_id": ..., "label": ..., "source": ..., "reason": "ontology_terminal_exact"}`
   * Repair loop behavior changes (guard only, no new decisions):

     * Do not schedule repair attempts targeting locked fields.
     * If a repair output returns a multi-field JSON that changes a locked field, ignore those changes and keep the canonical value.

4. **Audit trace (diagnostics-only)**
   Add structured fields to `audit.jsonl` (do not change final output schema):

   * `canonicalizations`: per field:

     * `field`, `original_value`, `canonical_value`, `term_id`, `source`, `match_type`
   * `locked_fields`: list or map
   * Ensure this adds no free-text rationale.

5. **Compatibility**

   * If canonicalization is enabled but locking is disabled:

     * Canonicalize value, but repairs may still adjust it later.
   * If locking is enabled but canonicalization is disabled:

     * Lock current value only if it already equals canonical label? (Make this explicit.)
     * Preferred: if locking is enabled, perform canonicalization implicitly for locked fields to avoid freezing a non-canonical string. If you choose this, document it and test it.

### Out of scope

* Changing final output schema to include term IDs
* Adding grounded labels/constraints into repair prompts (future ticket if needed)
* Changing decision routing or failure thresholds
* Introducing persistence or learning

---

## Acceptance Criteria

1. With both flags enabled, a terminal exact ontology match results in:

   * final output value equals `matched_label` (canonical label)
   * that field is not modified by later repair steps
2. Canonicalization is deterministic and auditable:

   * audit records show original vs canonical and term metadata
3. With flags disabled (default), behavior is unchanged.
4. All tests pass; new tests cover canonicalization and lock enforcement.

---

## Tests Required

Add `tests/test_ontology_canonicalize_and_lock.py`:

1. **Canonicalize on terminal exact**

   * Given a match:

     * `status="MATCHED"`, `score=1.0`, `match_type="label_norm_exact"`
     * `matched_label="Myc-CaP"`
     * original `output["cell_line"]="Myccap"`
   * With canonicalization enabled:

     * assert output becomes `"Myc-CaP"`

2. **Lock prevents repair overwrite**

   * Simulate a repair output that attempts to change `cell_line` to `"Myccap"` or something else.
   * With locking enabled:

     * assert final output remains `"Myc-CaP"`
     * assert no additional repair attempts are scheduled for `cell_line` (if repair planning is testable)

3. **Default-off regression**

   * With both flags disabled:

     * assert output remains original and repair can modify as before.

4. **Multi-field repair output guard**

   * Repair output JSON includes changes to multiple fields, including a locked one.
   * Assert only unlocked fields apply.

---

## Implementation notes

* Keep canonicalization/locking as a small, local addition:

  * Prefer a helper like:

    * `apply_terminal_exact_canonicalization_and_lock(state, ontology_matches, config)`
* The lock enforcement should be in the single place where repair outputs are merged into the current output (so it covers all repair templates).
* Ensure ordering is deterministic and does not depend on dict iteration order.

---

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-54.md` and paste this ticket verbatim.
