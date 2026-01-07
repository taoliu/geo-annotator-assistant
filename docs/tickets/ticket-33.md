## Ticket #33: CURATION-001 — Define `overrides.jsonl` schema and loader (no application yet)

### Background

v0.4 introduces **human-in-the-loop curation**.
To preserve determinism and auditability, all human corrections must be expressed as an **explicit input artifact**, not hidden state.

This ticket defines the **`overrides.jsonl` schema** and implements a **strict loader + validator**, without applying overrides to outputs yet.

This establishes the contract between:

* future UI tools
* CLI workflows
* the deterministic pipeline

---

### Scope (STRICT)

**In scope**

* Define `overrides.jsonl` schema
* Implement loader and validation
* Clear error reporting for invalid overrides
* Unit tests for schema and parsing

**Out of scope**

* Applying overrides to pipeline outputs
* Any behavior change to GSM annotation
* UI implementation
* Persistence beyond file input

---

### Goals

1. Establish a **stable, explicit format** for human edits
2. Make overrides **machine-validated**
3. Ensure overrides are **traceable and auditable**
4. Keep pipeline behavior unchanged until a later ticket

---

### Proposed `overrides.jsonl` Schema (v1)

One JSON object per line.

Required fields:

```json
{
  "gsm_accession": "GSM123456",
  "field": "organism",
  "new_value": "Homo sapiens"
}
```

Optional fields (recommended but not required):

```json
{
  "gsm_accession": "GSM123456",
  "field": "organism",
  "new_value": "Homo sapiens",
  "reason": "Curator confirmed from GEO description",
  "curator": "initials_or_id",
  "timestamp": "2026-01-07T10:30:00Z"
}
```

---

### Validation Rules

The loader must enforce:

1. **gsm_accession**

   * Required
   * Must match `^GSM[0-9]+$`

2. **field**

   * Required
   * Must be one of the canonical 8 output fields
   * No aliases, no synonyms

3. **new_value**

   * Required
   * Must be non-null
   * Type: string or list of strings (match output conventions)

4. **Unknown keys**

   * Allowed but ignored (future-proofing)
   * Must not break parsing

5. **Duplicates**

   * Multiple overrides for the same `(gsm_accession, field)`:

     * Loader must detect and raise a clear error

---

### Loader Behavior

Implement a loader, for example:

```python
load_overrides(path: str) -> Dict[(gsm_accession, field), OverrideRecord]
```

Behavior:

* Parse JSONL line by line
* Validate each record independently
* Accumulate errors and report all at once (not fail-fast)
* Return a normalized internal structure suitable for later application

No pipeline logic should consume this yet.

---

### Error Handling

Errors must be:

* Explicit
* Actionable
* Line-number aware

Example error message:

```
Invalid overrides.jsonl:
Line 4: field 'organisms' is not a valid output field
Line 9: duplicate override for (GSM123456, organism)
```

---

### Logging

When overrides are loaded:

```
[OVERRIDES] Loaded 12 override records from overrides.jsonl
```

No warnings or logs if no overrides file is provided (that is handled in later tickets).

---

### Acceptance Criteria

**Functional**

* Loader accepts valid `overrides.jsonl`
* Loader rejects invalid schema with clear messages
* Duplicate `(gsm_accession, field)` overrides are detected

**Correctness**

* Loader output is deterministic
* Unknown optional keys do not affect parsing

**Isolation**

* No changes to pipeline outputs
* No overrides applied anywhere

---

### Tests Required

1. **Valid input**

   * Single override
   * Multiple GSMs
   * Optional fields present

2. **Invalid input**

   * Invalid GSM accession
   * Invalid field name
   * Missing required keys
   * Duplicate overrides

3. **Edge cases**

   * Empty file
   * Comments or blank lines (if allowed; decide and document)

---

### Non-Goals (Explicit)

* No override application
* No ontology validation of `new_value`
* No UI
* No persistence or DB

---

### Documentation Updates

* Add a short section to:

  * `docs/whitepaper.md` or
  * `docs/RESUME.md`

Describing:

* Overrides as explicit human input
* Schema reference (high level, not full spec)

---

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-33.md` and paste this ticket verbatim.

---

### Codex working-note (MANDATORY)

At the start of the Codex session:

> **Working on ticket-33**

This note must remain visible in:

* Codex session notes
* Commit messages related to this ticket
