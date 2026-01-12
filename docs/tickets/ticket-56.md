# Ticket #56: CLI-STD-001 — Add deterministic `standardize-terms` command for ontology grounding and canonicalization

## Background

Curators may manually annotate GSM metadata outside the main pipeline and later request **term standardization** against the project’s ontologies.

The system already contains deterministic ontology grounding and canonicalization logic (post-v0.6) that is suitable for reuse **without invoking LLMs, repair loops, or decision routing**.

This ticket introduces a **standalone CLI command** to standardize curator-provided annotations while preserving all architectural invariants.

---

## Scope (STRICT)

### In scope

1. **New CLI subcommand: `standardize-terms`**

   * Accept curator-provided GSM annotations
   * Run ontology grounding and (optionally) canonicalization
   * Emit standardized outputs plus audit diagnostics

2. **Input format**

   * JSONL input

   * Each row must contain the **exact 8 GSM fields**:

     ```
     gse_accession
     gsm_accession
     data_type
     organism
     tissue_type
     cell_line
     disease
     treatment
     ```

   * Extra keys may be ignored but must not appear in outputs.

3. **Fields eligible for grounding**

   * Only fields with existing ontology grounders:

     * `data_type`
     * `tissue_type`
     * `cell_line`
     * `disease`
   * Other fields are passed through unchanged.

4. **Canonicalization behavior**

   * Reuse existing canonicalization helpers.
   * Canonicalization must be:

     * config-gated
     * deterministic
     * applied **only** when the grounding result is terminal exact
   * If canonicalization is disabled, grounding still runs but values are not replaced.

5. **Audit output**

   Emit a diagnostics-only audit JSONL (parallel to input rows) containing per-field grounding metadata:

   * status
   * score
   * match_type
   * ontology source
   * canonical_label_used (if any)
   * locked (if applicable)

   No free-text rationale.

6. **No backend side effects**

   * No LLM calls
   * No repair loops
   * No decision routing
   * No persistence
   * No learning
   * No schema changes

---

## Explicitly Out of Scope

* UI changes
* Any modification to:

  * pipeline ordering
  * repair logic
  * ontology semantics
  * RAG behavior
* CSV support (may be added later)
* Cross-GSM logic

---

## CLI Interface (Proposed)

Example usage:

```
uv run python -m agent.cli standardize-terms \
  --input curated.jsonl \
  --output curated.standardized.jsonl \
  --audit curated.standardized.audit.jsonl \
  --config config/example_config.yaml \
  --fields data_type,tissue_type,cell_line,disease \
  --canonicalize true
```

Rules:

* `--fields` defaults to all supported ontology-backed fields.
* Output JSONL must contain **exactly the same 8 fields** as input.
* Ordering of rows must be preserved.

---

## Acceptance Criteria

1. Given identical input and config, output is byte-for-byte deterministic.
2. Terminal exact matches are canonicalized **only when enabled**.
3. Non-terminal or ambiguous matches do not alter values.
4. Fields not listed in `--fields` are unchanged.
5. No existing backend tests fail.

---

## Tests Required

Add unit tests under `tests/`:

1. **Terminal exact canonicalization**

   * Input with known exact ontology match
   * Canonicalization enabled → value replaced
2. **Canonicalization disabled**

   * Same input
   * Canonicalization disabled → value unchanged
3. **Field selection**

   * Field excluded from `--fields` remains unchanged
4. **Schema enforcement**

   * Output contains exactly 8 fields per row

All tests must pass via:

```
uv run pytest -q
```

---

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-56.md` and paste this ticket **verbatim**.

---

If you want, the next step can be to **review whether this command should reuse `validator/grounders` directly or via a thin wrapper**, but that discussion should happen *after* this ticket is accepted.
