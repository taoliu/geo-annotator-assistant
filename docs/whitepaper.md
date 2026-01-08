# GEO GSM Annotator Agent — Whitepaper (v0.3)

## 1. Purpose and Scope

The GEO GSM Annotator Agent is a semi-automated system for extracting, validating, repairing, and standardizing **sample-level (GSM)** metadata from the GEO database using:

* large language models (LLMs),
* deterministic validators,
* ontology grounding,
* and bounded repair loops.

This document defines the **long-term architectural intent, invariants, and governance rules** of the project, updated to reflect the **v0.3 milestone**.

This document is **not**:

* an implementation guide,
* an API reference,
* a configuration manual.

The whitepaper is designed to remain valid across:

* multiple implementation iterations,
* multiple AI-assisted development sessions,
* and multiple contributors (human or AI).

---

## 2. Design Philosophy

The system is built around the following principles:

1. **LLMs propose; deterministic logic decides**
   LLMs generate candidate annotations only.
   All acceptance, repair, fallback, and escalation decisions are deterministic.

2. **Evidence over fluency**
   A fluent answer without textual support is worse than an incomplete answer.
   Unsupported inferences must be detected and corrected.

3. **Repair over rejection**
   Errors are routed to targeted, field-scoped repair whenever possible.

4. **Auditability over optimization**
   Every decision must be explainable post hoc through structured audit logs.

5. **Separation of time scales**

   * Long-term: architectural invariants (this document)
   * Medium-term: milestones (what exists and why)
   * Short-term: tickets (exact work to perform)

---

## 3. Core Output Contract (Invariant)

The agent produces **exactly eight output fields** per GSM record:

* `gse_accession`
* `gsm_accession`
* `data_type`
* `organism`
* `tissue_type`
* `cell_line`
* `disease`
* `treatment`

This schema is **immutable** within v0.x.

Validators, ontology grounding, and repair logic **must not change this schema**.

Any additional information must be recorded in **audit logs**, never in the final output.

---

## 4. End-to-End Data Flow Contract (Invariant)

The canonical processing pipeline is:

1. Context ingestion
2. Prompt construction
3. LLM generation
4. Format validation
5. Semantic validation
6. Ontology grounding
7. Decision routing
8. Repair loop (optional, bounded)
9. Final decision
10. Audit emission

Steps must occur **in this order**.

v0.3 explicitly wires and enforces this ordering in production code.

---

## 5. Validation and Repair Model (Invariant)

Validation failures are categorized into distinct classes:

* format violations,
* semantic inconsistencies,
* unsupported inferences,
* ontology grounding failures,
* cross-field consistency violations.

At each iteration:

* **Exactly one primary failure** is selected deterministically.
* A decision table maps that failure to one of:

  * `ACCEPT`
  * `REPAIR`
  * `FALLBACK`
  * `ESCALATE`

### v0.3 Guarantees

* Repairs are **field-scoped**, never global.
* Repairs are **attempt-bounded** per field.
* Repair loops are **globally bounded**.
* **Terminal fallback values** (for example `Unknown`, `No`) are respected.
* **Anti-cycling constraint**: once a field reaches a terminal fallback, it must not be repaired again in the same run.

---

## 6. Evidence-First Semantics (Invariant)

The system enforces an **evidence-first rule**:

> If a field value is inferred without explicit support in the GEO context, this failure must be resolved **before** ontology confidence is considered.

Implications:

* Unsupported inference dominates ontology ambiguity.
* Ontology grounding must never legitimize hallucinated values.
* Repair may neutralize values (for example fallback to `Unknown`) before ontology runs.

This rule is enforced by **deterministic failure prioritization**, not prompt wording.

---

## 7. Ontology Grounding Model (Invariant)

Ontology grounding is a **validation and normalization step**, not a generative step.

Invariants:

* Ontologies are externally built and read-only.

* The agent never mutates ontology databases.

* Grounding yields:

  * confident matches,
  * or structured failure states (no match, low confidence, ambiguous, skipped).

* Ontology results influence decisions but **do not directly mutate output fields**.

v0.3 uses Chroma-backed vector search with deterministic thresholds.

---

## 8. Retrieval and RAG Invariants

Retrieval-Augmented Generation (RAG) is used **only for candidate retrieval**, never for decision making.

Invariants:

* Retrieval is deterministic and auditable.
* Vector databases are queried read-only.
* Retrieved candidates are inputs to deterministic logic.
* No runtime learning or state mutation occurs.

---

## 9. GSE-Level Processing and Consistency (v0.3)

v0.3 introduces **GSE-aware execution**, including:

* GSE → GSM expansion via SOFT or JSONL ingestion,
* per-GSM independent labeling,
* GSE-level summary reporting.

Important constraint:

> **Labels are never blindly propagated across GSMs.**

Even within the same GSE:

* `data_type` may differ,
* `organism` may differ in rare or legacy datasets,
* tissue and disease annotations remain GSM-specific.

Only **diagnostic reporting** is shared at the GSE level, not labels.

---

## 10. Missing and Unknown Information (Policy Boundary)

Architecture guarantees:

* Missing or unsupported information is detected.
* Such cases are routed through repair or fallback deterministically.

Policy decisions such as:

* when to use `Unknown` vs `No`,
* whether `Healthy` is allowed without evidence,
* which fields allow explicit negatives,

are **milestone-scoped**, not architectural invariants.

v0.3 intentionally keeps these policies conservative.

---

## 11. Configuration Governance (Invariant)

### Canonical Namespace

All retrieval and ontology configuration **must** live under:

```
rag.*
rag.ontology.*
```

New top-level namespaces for retrieval or grounding are prohibited.

### Stability Rules

Any configuration change requires:

* updating example configs,
* updating config loaders,
* and at least one config-loading test.

---

## 12. Ticketing and Development Contract (Invariant)

All development work is tracked via numbered tickets.

Rules:

* Every ticket must exist as:

  ```
  docs/tickets/ticket-XXX.md
  ```

* Tickets must include:

  * context,
  * goals,
  * non-goals,
  * file-level tasks,
  * acceptance criteria.

Code changes without a ticket are invalid.

---

## 13. Audit and Explainability (Invariant)

The system must emit structured audit records capturing:

* raw LLM outputs,
* parsed outputs,
* validation results,
* ontology candidates,
* repair attempts,
* terminal fallbacks,
* final decisions.

Audit output is a **first-class artifact** and must never be disabled.

---

## 14. Known Limitations Deferred to v0.4

The following are **explicitly deferred**, not missing:

* interactive curator UI,
* human-in-the-loop correction workflows,
* cross-GSM consensus voting,
* curator feedback learning.

These require a different design surface and are out of scope for v0.3.

---

## 15. Summary

This document defines what **must remain true** even as the system evolves.

* The whitepaper defines **law**.
* Milestones define **state**.
* Tickets define **work**.

v0.3 establishes a stable, auditable, and curator-ready backend suitable for real GEO datasets, while intentionally deferring UI-level concerns to v0.4.

---

## 16. Human-in-the-Loop Governance (v0.4)

Starting in v0.4, the system formally supports **human-in-the-loop correction**, subject to strict architectural constraints.

The core principle is:

> Human judgment may *override* automated outputs, but must never *silently alter* system behavior.

Accordingly:

* Human corrections are treated as **explicit external inputs**, not internal state.
* Corrections must be **replayable, auditable, and deterministic**.
* Automated inference, validation, repair, and grounding logic remain unchanged.

Human involvement is therefore **governed**, not interactive or implicit.

---

## 17. Explicit Overrides as First-Class Inputs (v0.4)

v0.4 introduces an explicit override mechanism to represent curator decisions.

### Architectural invariants

* Overrides are provided as **versioned input artifacts**.
* Overrides apply **only after** all automated processing has completed.
* Overrides must not trigger:

  * new inference,
  * additional repair,
  * ontology re-grounding,
  * or cross-GSM propagation.

Overrides affect only the **final output values** and are recorded verbatim in audit logs, including:

* the original value,
* the overridden value,
* and optional curator metadata.

This design ensures that human judgment is:

* transparent,
* repeatable,
* and clearly separable from automated reasoning.

---

## 18. Structured Review Artifacts (v0.4)

v0.4 formalizes a set of **machine-readable review artifacts** intended to support curation workflows and downstream tooling.

These artifacts expose *what the system decided* and *why*, without changing decisions.

### Curator summary outputs

* Tabular and structured summaries present final GSM-level outputs.
* Structured formats are defined as **lossless mirrors** of curator-facing tables.
* No additional semantics are introduced beyond what is already decided by the pipeline.

### Structural diagnostic evidence

v0.4 introduces **structural evidence diagnostics**, derived solely from existing audit signals, including:

* number of repair attempts per field,
* terminal fallback usage,
* ontology grounding status,
* field-relevant diagnostic flags.

Importantly:

* No free-text explanations are generated.
* No new inference is performed.
* Evidence is diagnostic, not justificatory prose.

This preserves determinism while enabling informed human review.

---

## 19. Cross-GSM Signals as Advisory Information (v0.4)

v0.4 allows the system to compute **cross-GSM diagnostic signals**, subject to strict non-forcing rules.

Key constraints:

* GSMs remain **independent decision units**.
* No labels are automatically propagated across GSMs.
* Aggregation is **diagnostic only**, never prescriptive.

Cross-GSM analysis may surface:

* majority outliers,
* singleton values,
* internal inconsistencies within a GSE.

These signals are **advisory**, opt-in, and explicitly separated from final outputs.

---

## 20. Performance as an Architectural Requirement (v0.4)

v0.4 elevates **performance stability** to an architectural concern.

Specifically:

* GSE-scale processing must be feasible on a single accelerator device.
* Performance optimizations must not alter:

  * inference semantics,
  * decision ordering,
  * or determinism guarantees.

Performance improvements are therefore treated as **behavior-preserving transformations**, not algorithmic changes.

---

## 21. Updated Boundary of Deferred Concerns

With v0.4, the following concerns remain **explicitly deferred**:

* interactive or web-based curator UI,
* persistent or collaborative curation state,
* learning from human edits,
* automated consensus enforcement across GSMs.

These are intentionally excluded from the long-term architecture and require separate governance.

---

## 22. Updated Summary

With the additions in v0.4, the system now satisfies the following long-term properties:

* Fully deterministic automated annotation
* Explicit, auditable human correction
* Structured, machine-readable review artifacts
* Advisory (non-forcing) cross-GSM diagnostics
* Performance stability at GSE scale

The architectural contract remains unchanged:

* The whitepaper defines **what must remain true**.
* Milestones define **what exists at a given time**.
* Tickets define **what work is permitted**.

v0.4 closes the backend phase of development and establishes a stable foundation for curator-facing interfaces in subsequent milestones.

---
