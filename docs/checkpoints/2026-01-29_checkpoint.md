# Checkpoint — 2026-01-29 (v0.9)

## Project

geo-gsm-annotator-agent

## Milestone Status

**v0.9 — Validation, Repair, and Policy Consolidation**

Milestone v0.9 is complete. This checkpoint captures the authoritative system behavior after extensive real-world testing on heterogeneous GEO datasets and consolidation of validation and repair policies.

---

## System Scope at This Checkpoint

The system performs:

* LLM-based extraction of 8 canonical metadata fields from GEO GSM records
* Deterministic validation, ontology grounding, repair, and flagging
* Curator-facing outputs with explicit failure rationales

UI work is out of scope for v0.9.

---

## Core Pipeline (Authoritative)

1. **LLM Extraction**

   * Produces a single JSON object with exactly 8 fields
   * LLM is treated as a *suggestion generator*, not an authority

2. **Validation Layer**

   * Format validation (schema, word limits, illegal placeholders)
   * Semantic validation (field misuse, inferred disease, identity leakage)

3. **Ontology Grounding**

   * data_type → EFO
   * tissue_type → Uberon
   * cell_line → Cellosaurus
   * disease → DOID, with NCIT fallback enabled for cancer terms

4. **Repair Loop**

   * Deterministic first
   * LLM-based only when explicitly allowed
   * Hard caps on attempts per field

5. **Final Decision**

   * ACCEPT or FLAGGED
   * All FLAGGED outputs carry explicit machine-readable reasons

---

## Policy Formalization (New in v0.9)

v0.9 introduces **explicit, written policies** governing repair and flagging behavior. These policies are now first-class system invariants.

Canonical policy categories:

### 1. Disease Generalization Policy

* Sloppy disease strings (e.g. "Lung Tumor") are deterministically generalized when a clear ontology target exists (e.g. lung cancer)
* DOID is preferred; NCIT is used when appropriate
* Low-confidence matches are FLAGGED, not silently accepted

### 2. Tissue Type Site-vs-Origin Disambiguation

* tissue_type must be anatomical (Uberon)
* Non-anatomical values (e.g. Tumor, Lymphoma) are treated as placeholders
* Such cases are explicitly FLAGGED for curator review

### 3. Non-Anatomical Placeholder Handling

* Explicit registry for placeholders (e.g. Tumor, Unknown, Not sure)
* Placeholder values do not pass ontology matching
* They trigger deterministic flags, not LLM retries

### 4. Healthy / Control Disease Policy

* "Healthy", "Healthy donor", and similar labels are **not diseases**
* These values are allowed but always FLAGGED
* No forced ontology mapping is attempted

### 5. Model vs Disease Separation

* Model names (e.g. CT26 mouse tumor model) are preserved
* Optional generalization is deterministic and conservative
* No speculative disease inference

### 6. Cell Line Resolution Policy

* Exact Cellosaurus matches are preferred
* Ambiguity is resolved deterministically when possible
* True ambiguity is FLAGGED

### 7. Treatment Field Policy

* Identity leakage (sample IDs, subset labels) is detected
* If no safe repair exists, treatment is set to None
* Missing repair templates do **not** block ACCEPT

---

## Flagging Philosophy (Authoritative)

* FLAGGED does **not** mean incorrect
* FLAGGED means "requires human awareness"
* No silent auto-corrections for ambiguous biology

Each flag is:

* Deterministic
* Reproducible
* Traceable to a written policy

---

## Determinism Guarantees

At this checkpoint:

* No infinite repair loops
* No policy-dependent randomness
* Cache-safe behavior for LLM and grounding layers

---

## Known Limitations (Intentional)

The following are explicitly deferred beyond v0.9:

* Cross-GSM consistency enforcement within a GSE
* Deep disease subtyping beyond submitter intent
* Automatic separation of host tissue vs tumor microenvironment
* UI-based curator workflows

---

## Artifacts Added in v0.9

* `docs/policies/` directory
* Consolidated written policies covering tickets #84–#99
* Policy-first ticketing guidance

---

## Transition Guidance

Future milestones must:

* Treat written policies as authoritative
* Update policy documents when behavior changes
* Avoid embedding new logic without policy justification

---

**Checkpoint status:** CLOSED
