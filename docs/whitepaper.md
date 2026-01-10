# GEO GSM Annotator Agent — Whitepaper

## 1. Purpose and Scope

The GEO GSM Annotator Agent is a semi-automated system for extracting,
validating, repairing, and standardizing **sample-level (GSM)** metadata
from the GEO database using:

* large language models (LLMs),
* deterministic validators,
* ontology grounding,
* bounded repair loops,
* and explicit human overrides.

This document defines the **long-term architectural intent, invariants,
and governance rules** of the project.

It is explicitly **not**:

* an implementation guide,
* an API reference,
* a UI specification,
* or a configuration manual.

The whitepaper is intended to remain valid across:

* multiple implementation iterations,
* multiple AI-assisted development sessions,
* and multiple contributors (human or AI).

---

## 2. Design Philosophy

The system is governed by the following principles:

1. **LLMs propose; deterministic logic decides**
   LLMs generate candidate annotations only.
   All acceptance, repair, fallback, and escalation decisions are deterministic.

2. **Evidence over fluency**
   A fluent answer without explicit support is worse than an incomplete answer.
   Unsupported inferences must be detected and resolved.

3. **Repair over rejection**
   Errors are routed to targeted, field-scoped repair whenever possible.

4. **Auditability over optimization**
   Every decision must be explainable post hoc through structured audit artifacts.

5. **Separation of time scales**

   * Whitepaper: architectural law
   * Milestones: system state
   * Tickets: permitted work

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

No additional fields may appear in final outputs.
Any extra information must be recorded in **audit artifacts** only.

---

## 4. End-to-End Processing Contract (Invariant)

The canonical pipeline is:

1. Context ingestion
2. Prompt construction
3. LLM generation
4. Format validation
5. Semantic validation
6. Ontology grounding
7. Deterministic decision routing
8. Bounded repair loop (optional)
9. Final decision
10. Audit emission

This ordering is mandatory and must not be altered.

---

## 5. Validation and Repair Model (Invariant)

Failures are categorized into deterministic classes:

* format violations
* semantic inconsistencies
* unsupported inferences
* ontology grounding failures
* cross-field consistency violations

At each iteration:

* **Exactly one primary failure** is selected deterministically
* A decision table maps it to:

  * `ACCEPT`
  * `REPAIR`
  * `FALLBACK`
  * `ESCALATE`

### Repair guarantees

* Repairs are field-scoped
* Repairs are attempt-bounded per field
* Repair loops are globally bounded
* Terminal fallback values are respected
* Anti-cycling constraints are enforced

---

## 6. Evidence-First Semantics (Invariant)

The system enforces an **evidence-first rule**:

> Unsupported inference must be resolved before ontology confidence
> or normalization is considered.

Consequences:

* Ontology grounding must never legitimize hallucinated values
* Repair may neutralize values before ontology is consulted
* Failure prioritization is deterministic, not prompt-driven

---

## 7. Ontology Grounding Model (Invariant)

Ontology grounding is a **validation and normalization step**, not a
generative step.

Invariants:

* Ontologies are externally built and read-only
* The agent never mutates ontology databases
* Grounding yields structured outcomes:

  * confident match
  * no match
  * ambiguous
  * low confidence

### Terminal exact matches

Grounding may produce **terminal exact matches**, defined as deterministic
matches with full confidence.

When a terminal exact match is identified:

* The ontology’s canonical label **may be used to normalize the output value**
* Normalization is deterministic and auditable
* Normalization does not constitute inference or decision-making

Canonicalization and any associated safeguards must not violate the
core output schema or decision ordering.

---

## 8. Retrieval and RAG Invariants

Retrieval-Augmented Generation (RAG):

* is deterministic and auditable
* is read-only
* supplies candidates only
* never makes decisions
* never learns or mutates state

### Deterministic-first retrieval

Ontology retrieval must prioritize **deterministic exact matches**
before any approximate or vector-based methods.

Consequences:

* Exact metadata or identifier matches must short-circuit further retrieval
* Vector similarity search is **fallback-only**
* Retrieval optimizations must preserve determinism and ordering

---

## 9. GSM and GSE Independence (Invariant)

* GSMs are independent decision units
* GSE processing expands into GSMs
* No label propagation is permitted across GSMs

Cross-GSM analysis may exist only as **diagnostic, advisory information**.

---

## 10. Human Overrides as First-Class Inputs (Invariant)

Human judgment may override automated outputs, but must never silently alter
system behavior.

Architectural guarantees:

* Overrides are explicit input artifacts
* Overrides apply only after automated processing completes
* Overrides do not trigger:

  * re-inference
  * repair
  * ontology grounding
  * cross-GSM propagation
* Overrides are fully auditable and replayable

Human involvement is therefore **governed**, not implicit.

---

## 11. Review Artifacts and Diagnostics (Invariant)

The system emits structured, machine-readable artifacts exposing decisions
without altering them.

These include:

* lossless output mirrors
* structural diagnostic evidence
* advisory cross-GSM signals
* mandatory audit logs

No free-text rationale is generated.
No new inference is introduced.

---

## 12. Performance as an Architectural Requirement (Invariant)

Performance stability is a first-class architectural concern.

Requirements:

* GSE-scale processing must be feasible on a single accelerator
* Performance optimizations must preserve:

  * inference semantics
  * decision ordering
  * determinism

Avoiding unnecessary computation (for example, redundant retrieval or
embedding calls) is a valid and encouraged optimization when behavior is
preserved.

---

## 13. Configuration Governance (Invariant)

* Retrieval and ontology configuration must live under:

```
rag.*
rag.ontology.*
```

* New namespaces for retrieval or grounding are prohibited
* Config changes require tests and example updates

---

## 14. Development Governance (Invariant)

* All work is tracked via numbered tickets
* Code changes without a ticket are invalid
* Whitepaper defines law
* Milestones define state
* Tickets define work

---

## 15. Explicitly Non-Architectural Concerns

The following are intentionally excluded from architectural governance:

* curator UI implementation
* visualization choices
* persistence layers
* collaboration features
* learning from human edits

These may exist but must not violate architectural invariants.

---

## 16. Summary

This whitepaper defines **what must remain true** regardless of
implementation changes.

It prioritizes:

* determinism
* auditability
* explicit human control
* strict separation of concerns

As long as these invariants hold, the system may evolve safely.
