# Ticket #55: RAG-ONTO-012 — Disease fallback DOID→NCIT gated by configurable malignant-neoplasm trigger

## Background

NCIT supplements DOID for detailed malignant neoplasm terms. To avoid over-triggering NCIT, we gate NCIT queries behind a **deterministic lexical trigger**, now configurable by the user.

---

## Scope (STRICT)

### In scope

1. **Two-stage disease ontology strategy**

   * Stage 1: query DOID (`source="Human Disease Ontology"`)
   * Stage 2: query NCIT **only if**:

     * DOID is not terminal exact, and
     * disease label satisfies malignant-neoplasm trigger

2. **Terminal exact predicate**
   Reuse shared helper (from Ticket #53):

```python
is_terminal_exact(status, score, match_type)
```

3. **Configurable malignant-neoplasm trigger**

Add config key:

```yaml
rag:
  ontology:
    disease:
      ncit_fallback:
        enabled: true
        trigger_terms:
          - cancer
          - tumor
          - tumour
          - carcinoma
          - adenocarcinoma
          - sarcoma
          - neoplasm
          - malignan
          - metastat
          - leukemia
          - lymphoma
          - myeloma
          - glioma
          - glioblastoma
          - melanoma
          - blastoma
```

Implementation requirements:

* Trigger check is **pure, deterministic**, no embeddings
* Case-insensitive substring match
* No token splitting
* Empty or missing `trigger_terms` ⇒ NCIT never triggered
* `enabled: false` ⇒ NCIT never triggered

Reference implementation:

```python
def should_query_ncit(raw_label: str, trigger_terms: list[str]) -> bool:
    s = raw_label.lower()
    return any(t in s for t in trigger_terms)
```

4. **Selection rule (deterministic)**

* If DOID terminal exact → select DOID, stop
* Else if NCIT fallback disabled or trigger false → keep DOID result
* Else query NCIT:

  * If NCIT terminal exact → select NCIT
  * Else deterministic tie-break:

    1. higher score wins
    2. if tie, prefer DOID (default, conservative)

5. **Audit additions (diagnostics-only)**

Under disease grounding record:

* `ncit_fallback_enabled`
* `ncit_triggered`
* `ncit_trigger_terms_used`
* `attempted_sources`
* `selected_source`
* `selection_rule`

No free-text rationale.

6. **Canonicalization / locking**
   Apply Ticket #54 behavior to the **selected** ontology match (DOID or NCIT), when enabled.

---

## Acceptance Criteria

1. Default config triggers NCIT for cancer-like terms but not for non-neoplastic diseases.
2. Users can extend `trigger_terms` without code changes.
3. Deterministic behavior across runs.
4. Existing tests pass; new tests validate config-driven triggering.

---

## Tests Required

Add `tests/test_disease_ncit_trigger_configurable.py`:

1. Default trigger list:

   * “metastatic castration-resistant prostate cancer” → trigger true
2. Custom trigger list:

   * config adds `"mycosis"` → trigger true only when configured
3. Disabled fallback:

   * `enabled: false` → NCIT never queried
4. Empty trigger list:

   * NCIT never queried

---

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-55.md` and paste this ticket verbatim.

---
