# GEO GSM Annotator Agent — Whitepaper

## 1. Purpose and Scope

The GEO GSM Annotator Agent is a semi-automated system for extracting, validating, repairing, and standardizing sample-level metadata (GSM) from the GEO database using large language models (LLMs), deterministic validators, and ontology grounding.

This document defines the **long-term architectural intent, invariants, and governance rules** of the project.

It is intentionally **not**:

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
   LLMs generate candidate annotations. All acceptance, rejection, repair, or escalation decisions are made by deterministic code.

2. **Evidence over fluency**
   A fluent answer without textual support is worse than an incomplete answer. Unsupported inferences must be detected and corrected.

3. **Repair over rejection**
   When possible, errors are routed to targeted repair rather than immediate failure.

4. **Auditability over optimization**
   Every decision must be explainable post hoc through structured audit records.

5. **Separation of time scales**

   * Long-term: architectural invariants (this document)
   * Medium-term: milestones (what exists and why)
   * Short-term: tickets (exact work to perform)

---

## 3. Core Output Contract (Invariant)

The agent produces **exactly eight output fields** per GSM record.

This schema is immutable unless explicitly revised by a new major milestone:

* `gse_accession`
* `gsm_accession`
* `data_type`
* `organism`
* `tissue_type`
* `cell_line`
* `disease`
* `treatment`

Validators, ontology grounding, and repair logic **must not change this schema**.

Any additional information must be recorded in audit logs, not in the final output.

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

Reordering steps requires an explicit milestone-level decision.

---

## 5. Validation and Repair Model (Invariant)

Validation failures are categorized into distinct classes, including:

* format violations,
* semantic inconsistencies,
* unsupported inferences,
* ontology grounding failures.

At each iteration:

* Exactly **one primary failure** is selected deterministically.
* A decision table maps the failure to one of:

  * ACCEPT
  * REPAIR
  * FALLBACK
  * ESCALATE

Repair is **field-targeted**, **bounded**, and **auditable**.

---

## 6. Evidence-First Semantics (Invariant)

The system enforces an **evidence-first rule**:

> If a field value is inferred without explicit support in the GEO context, this failure must be addressed **before** any ontology confidence issues.

Implications:

* Unsupported inferences take precedence over ontology ambiguity or low confidence.
* Ontology grounding must never legitimize hallucinated values.
* Evidence-based repair may remove or neutralize values before ontology validation runs.

This rule is enforced at the failure-selection level, not via ad hoc prompt logic.

---

## 7. Ontology Grounding Model (Invariant)

Ontology grounding is a **validation and normalization step**, not a generative step.

Invariants:

* Ontologies are externally built, read-only resources.
* The agent does not modify ontology databases.
* Grounding yields:

  * confident matches,
  * or structured failure states (no match, ambiguous, low confidence, skipped).
* Grounding influences decisions but does not directly mutate output fields.

Ontology confidence must never override evidence constraints.

---

## 8. Retrieval and RAG Invariants

Retrieval-Augmented Generation (RAG) is used **only for candidate retrieval**.

Invariants:

* Retrieval is deterministic and auditable.
* Vector databases are queried in read-only mode.
* Query embeddings are computed explicitly by the agent.
* Retrieved candidates are inputs to deterministic selection logic.
* No implicit learning or state mutation occurs at runtime.

---

## 9. Missing and Unknown Information (Policy Boundary)

This system distinguishes **architecture** from **labeling policy**.

Architecture guarantees:

* Missing or unsupported information is detected.
* Such cases are routed through repair or fallback deterministically.

Policy decisions such as:

* whether to represent absence as `Unknown`, `No`, or `Healthy`,
* when a value may be inferred from context,
* which fields allow explicit negatives,

are **milestone-scoped**, not hard-coded as architectural invariants.

This prevents premature semantic lock-in.

---

## 10. Configuration Governance (Invariant)

### Canonical Namespace

All retrieval and ontology configuration **must** live under:

```
rag.*
rag.ontology.*
```

New top-level namespaces for retrieval or grounding are prohibited.

### Stability Rules

Any configuration change requires updating:

* config models,
* example configs,
* and at least one config-loading test.

---

## 11. Ticketing and Development Contract (Invariant)

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
  * explicit file-level tasks,
  * acceptance criteria.
* Code changes without an associated ticket are invalid.

---

## 12. Audit and Explainability (Invariant)

The system must emit structured audit records capturing:

* raw LLM outputs,
* parsed outputs,
* validation results,
* ontology candidates,
* repair attempts,
* final decisions.

Audit records are first-class outputs and must never be silently disabled.

---

## 13. Guidance for Future AI-Assisted Sessions

Before proposing changes, AI agents must:

1. Read this whitepaper.
2. Inspect current example configs.
3. Inspect existing milestones and tickets.
4. Follow established namespaces and contracts.

If a proposal conflicts with an invariant defined here, it must:

* explicitly state the conflict,
* justify the change,
* and be introduced via a milestone-level update.

---

## 14. Summary

This document defines what **must remain true** even as the system evolves.

* The whitepaper defines **law**.
* Milestones define **state**.
* Tickets define **work**.

This separation is essential for correctness, auditability, and continuity in a system developed across long time spans and multiple AI-assisted sessions.

---
