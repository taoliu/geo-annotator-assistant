# GEO GSM Annotator Agent — Whitepaper

## 1. Purpose and Scope

The GEO GSM Annotator Agent is a semi-automated system for extracting, validating, repairing, and standardizing **sample-level (GSM)** metadata from the GEO database.

The system combines:

* large language models (LLMs) for proposal generation,
* deterministic validators and decision logic,
* ontology grounding for normalization and confidence assessment,
* bounded, field-scoped repair loops,
* and explicit, auditable human overrides.

This document defines the **long-term architectural invariants and governance rules** of the project.

It is explicitly **not**:

* an implementation guide,
* a UI specification,
* an API reference,
* or a configuration manual.

The whitepaper is intended to remain valid across:

* multiple milestones,
* multiple AI-assisted development sessions,
* and multiple contributors.

---

## 2. Design Philosophy

The system is governed by the following principles:

1. **LLMs propose; deterministic logic decides**
   LLMs may suggest candidate annotations, but all acceptance, repair, fallback, and escalation decisions are deterministic.

2. **Evidence over fluency**
   Unsupported inferences are strictly disallowed, regardless of how fluent they appear.

3. **Repair over rejection**
   Errors are resolved via bounded, field-scoped repair whenever possible.

4. **Auditability over optimization**
   Every decision must be explainable through structured audit artifacts.

5. **Separation of time scales**

   * Whitepaper: architectural law
   * Milestones: medium-term system state
   * Tickets: permitted short-term work

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
All auxiliary information must be recorded only in **audit artifacts**.

---

## 4. End-to-End Processing Contract (Invariant)

The canonical pipeline order is:

1. Context ingestion
2. Prompt construction
3. LLM proposal generation
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

Failures are categorized deterministically into:

* format violations
* semantic inconsistencies
* unsupported inference
* ontology grounding failures
* cross-field consistency violations

At each iteration:

* exactly one primary failure is selected deterministically,
* a decision table maps it to one of:

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

### Repair vs Fallback Semantics

Repair is only attempted when:

* a field violates semantic constraints, or
* ontology validation fails in a **non-terminal** way.

Some values are treated as **terminal fallbacks by policy** and are never repaired.
These include values that are explicitly underspecified, non-anatomical, or curator-ambiguous.

Terminal fallback values are surfaced via explicit flags for human review rather than forced normalization.

---

## 6. Evidence-First Semantics (Invariant)

The system enforces an **evidence-first rule**:

> Unsupported inference must be resolved before ontology confidence or normalization is considered.

Consequences:

* Ontology grounding must never legitimize hallucinated values
* Repair may neutralize values before ontology is consulted
* Failure prioritization is deterministic and not prompt-driven

---

## 7. Ontology Grounding Model (Invariant)

Ontology grounding is a **validation and normalization step**, not a generative step.

Invariants:

* Ontologies are externally built and read-only
* The agent never mutates ontology databases
* Grounding yields structured outcomes:

  * confident match
  * ambiguous match
  * no match
  * low confidence

Ontology grounding never forces normalization.

A high-confidence ontology match may still be flagged if semantic intent is ambiguous, underspecified, or inconsistent with curator expectations.

Ontologies are used to assess confidence and surface ambiguity, not to overwrite curator-relevant meaning.

### Terminal exact matches

A terminal exact match is defined as a deterministic match with full confidence.

When identified:

* The ontology’s canonical label may be used to normalize the output value
* Canonicalization is deterministic and auditable
* Canonicalization does not constitute inference

---

## 8. Retrieval and RAG Invariants

Retrieval-Augmented Generation (RAG):

* is deterministic and auditable
* is read-only
* supplies candidates only
* never makes decisions
* never learns or mutates state

Exact matches must be prioritized over approximate retrieval.
Vector similarity search is **fallback-only**.

---

## 9. GSM and GSE Independence (Invariant)

* GSMs are independent decision units
* GSE processing expands into GSMs
* No label propagation is permitted across GSMs

Cross-GSM signals may exist only as advisory diagnostics.

---

## 10. Human Overrides as First-Class Inputs (Invariant)

Human judgment may override automated outputs, but must never silently alter system behavior.

Guarantees:

* Overrides are explicit input artifacts
* Overrides apply only after automated processing completes
* Overrides do not trigger re-inference, repair, or grounding
* Overrides are fully auditable and replayable

---

## 11. Review Artifacts and Diagnostics (Invariant)

The system emits structured artifacts exposing decisions without altering them.

These include:

* lossless output mirrors
* diagnostic evidence records
* advisory cross-GSM summaries
* mandatory audit logs

No free-text rationale is generated.

---

## 12. Performance as an Architectural Requirement (Invariant)

Performance stability is required:

* GSE-scale processing must be feasible on a single accelerator
* Optimizations must preserve determinism and semantics

Avoid unnecessary computation when behavior can be preserved.

---

## 13. Configuration Governance (Invariant)

* Retrieval and ontology configuration must live under:

```
rag.*
rag.ontology.*
```

* New namespaces are prohibited
* Config changes require tests and examples

---

## 14. Development Governance (Invariant)

* All work is ticketed
* Whitepaper defines law
* Milestones define system state
* Tickets define permitted work

---

## 15. Policy Layer (Explicit and Versioned)

The system includes an explicit **policy layer** that governs:

* validation rules
* repair triggering conditions
* terminal vs non-terminal fallbacks
* flagging and reporting semantics

Policies are **deterministic, versioned, and documented separately from implementation**.

Policies may evolve across milestones without changing:

* the output schema
* architectural invariants
* or backend execution order

The policy layer exists to make real-world behavior explicit, reviewable, and curator-trustworthy.

Detailed validation, repair, and reporting rules are defined in `docs/policies/` and are treated as authoritative within architectural constraints.

---

## 16. Explicitly Non-Architectural Concerns

The following are intentionally excluded from architectural governance:

* curator UI implementation
* visualization choices
* persistence layers
* collaboration features
* learning from human edits

---

## 17. Summary

This whitepaper defines **what must remain true** regardless of implementation changes.

As long as these invariants hold, the system may evolve safely.
