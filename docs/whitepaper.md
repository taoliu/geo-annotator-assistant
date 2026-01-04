# GEO GSM Annotator Agent — Whitepaper

## 1. Purpose and Scope

The GEO GSM Annotator Agent is a semi-automated system for extracting, validating, and standardizing sample-level metadata (GSM) from the GEO database using large language models (LLMs), deterministic validators, and ontology grounding.

This document defines the **long-term architectural intent, invariants, and governance rules** of the project.
It is not an implementation guide, API reference, or configuration manual.

The whitepaper is designed to remain valid across:

* multiple implementation iterations,
* multiple AI-assisted development sessions,
* and multiple contributors (human or AI).

---

## 2. Design Philosophy

The system is built around the following principles:

1. **LLMs generate, validators decide**
   LLMs propose annotations. Deterministic logic decides acceptance, repair, or rejection.

2. **Auditability over cleverness**
   Every decision must be explainable post hoc through structured audit records.

3. **Repair over rejection**
   When possible, errors should be routed to targeted repair rather than immediate failure.

4. **Separation of time scales**

   * Long-term: architectural invariants (this document)
   * Medium-term: milestones (what exists and why)
   * Short-term: tickets (exact changes)

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

1. **Context ingestion**
   Raw GEO GSM context is ingested as unstructured text.

2. **Prompt construction**
   Context is embedded into a structured prompt template.

3. **LLM generation**
   The LLM proposes a complete 8-field annotation.

4. **Format validation**
   Output is checked for schema and syntactic correctness.

5. **Semantic validation**
   Internal consistency and heuristic rules are applied.

6. **Ontology grounding**
   Selected fields are grounded against external ontologies.

7. **Decision routing**
   Validation results are mapped to actions using a decision table.

8. **Repair loop (optional)**
   Targeted LLM repair is invoked when allowed.

9. **Final decision**
   Output is accepted, flagged, or rejected.

10. **Audit emission**
    All steps, decisions, and alternatives are recorded.

Steps must occur **in this order**.
Reordering steps requires an explicit milestone-level decision.

---

## 5. Ontology Grounding Model (Invariant)

Ontology grounding is a **validation and decision-support step**, not a generative step.

Key invariants:

* Ontology resources are **read-only** and externally built.
* The agent does not modify ontology databases.
* Ontology grounding produces:

  * matched term ID and label (when confident),
  * or structured failure states (no match, ambiguous, low confidence).
* Grounding results influence decisions via validators and decision tables.
* Grounding does not directly change the final output schema.

---

## 6. Retrieval and RAG Invariants

Retrieval-Augmented Generation (RAG) is used only for **candidate retrieval**, never as an authority.

Invariants:

* Retrieval is deterministic and auditable.
* Vector databases are queried in read-only mode.
* Query embeddings are computed explicitly by the agent.
* Retrieval results are inputs to deterministic selection logic.
* No hidden state or implicit learning occurs at runtime.

---

## 7. Configuration Governance (Invariant)

### Canonical Namespace

All retrieval- and grounding-related configuration **must** live under:

```
rag.*
```

Ontology-specific configuration must live under:

```
rag.ontology.*
```

New top-level configuration namespaces for retrieval or grounding are prohibited.

### Stability Rules

* Example configs under `config/` define the canonical schema.
* Any change to configuration requires updating:

  * the config model code,
  * all example configs,
  * at least one config-loading test.

Backward compatibility is allowed only via explicit compatibility shims and warnings.

---

## 8. Ticketing and Development Contract (Invariant)

All development work is tracked via numbered tickets.

Rules:

* Every ticket must be written to a file under:

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

This contract ensures continuity across AI-assisted sessions.

---

## 9. Audit and Explainability (Invariant)

The system must emit structured audit records capturing:

* raw LLM outputs,
* parsed outputs,
* validation results,
* ontology candidates and decisions,
* repair attempts,
* final decisions.

Audit records are first-class outputs and must never be skipped or disabled silently.

---

## 10. Explicit Non-Goals

This whitepaper intentionally does **not** define:

* exact thresholds or numeric constants,
* specific ontology versions,
* specific LLM models,
* CLI flags or argument names,
* file paths or directory layouts,
* prompt wording.

These details belong to milestones or tickets and may change over time.

---

## 11. Guidance for Future AI-Assisted Sessions

Before proposing changes, future AI agents must:

1. Read this whitepaper.
2. Inspect current example configs.
3. Inspect existing tickets and milestones.
4. Follow established namespaces and contracts.

If a proposal conflicts with an invariant defined here, it must:

* explicitly state the conflict,
* justify the change,
* and be introduced via a milestone-level update.

---

## 12. Summary

This document defines what **must remain true** even as the code evolves.

* The whitepaper defines *law*.
* Milestones define *state*.
* Tickets define *work*.

This separation is essential for maintaining correctness, auditability, and continuity in a system developed across long time spans and multiple AI-assisted sessions.

---

