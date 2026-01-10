# AGENTS.md — Development Governance and Agent Roles

This document defines **how human developers, ChatGPT, and Codex CLI collaborate** on the GEO GSM Annotator Agent project.

It is a governance document, not an implementation guide.

---

## 1. Roles and Responsibilities

### ChatGPT (Architect / Reviewer)

ChatGPT acts as:

* system architect
* design reviewer
* ticket author
* documentation editor

Responsibilities:

* Define architectural intent and invariants
* Propose milestone plans and tickets
* Ensure determinism, auditability, and schema stability
* Review designs for unintended semantic changes
* Update whitepaper, milestones, checkpoints, and handoff docs

ChatGPT **does not**:

* implement production code
* bypass ticketing
* silently change system semantics

---

### Codex CLI (Implementer)

Codex CLI acts as:

* code implementer
* test author
* refactor executor

Responsibilities:

* Implement tickets verbatim
* Preserve architectural invariants
* Add or update tests as required by tickets
* Save tickets and changes as markdown artifacts

Codex CLI **must not**:

* introduce behavior not specified in a ticket
* redesign pipeline structure
* modify output schema
* remove audit signals

---

## 2. Architectural Invariants (Non-Negotiable)

All agents must respect the following invariants:

* Exactly **8 output fields** per GSM
* Deterministic decision routing
* Bounded repair loops
* Read-only, non-decisional RAG
* Fully auditable execution

Any change violating these invariants requires explicit approval
and a whitepaper update.

---

## 3. Ontology and RAG Governance (v0.6+)

### Deterministic-first retrieval

* Ontology retrieval must prioritize deterministic exact matches
* Vector similarity search is **fallback-only**
* Exact matches must short-circuit embedding and vector queries

### Terminal exact semantics

A terminal exact match is defined as:

* `status == MATCHED`
* `score == 1.0`
* exact match type (label, normalized label, synonym, or ID)

Terminal exact matches:

* may canonicalize output labels
* may lock fields against later repair
* must be auditable and config-gated

Agents must not bypass or weaken these semantics.

---

## 4. Embedding and Retrieval Implementation Notes

* ChromaDB collections may attach an embedding function when required
* Embedding device (`cpu`, `cuda`, `mps`) must respect configuration
* Avoid unnecessary embedding calls whenever behavior can be preserved

Older guidance that prohibited embedding functions in Chroma is
superseded by ticketed v0.6 decisions.

---

## 5. Ticket-Driven Development Model

* All changes must be associated with a numbered ticket
* Tickets define:

  * scope
  * constraints
  * acceptance criteria
  * required tests
* Code changes without tickets are invalid

Tickets are stored under `docs/tickets/` and are the
**only permitted mechanism** for altering code behavior.

### Testing requirement

Unless a ticket explicitly says otherwise, Codex must run unit tests with:

```
uv run pytest -q
```

If tests fail, fix them within the same ticket scope before reporting completion.

---

## 6. Documentation Hierarchy

Agents must respect the following authority order:

1. `docs/whitepaper.md` — architectural law
2. `docs/milestones/v*.md` — system state
3. `docs/checkpoints/xxxx-xx-xx_checkpoint.md`— handoff anchors
4. `docs/tickets/ticket-xx.md` — permitted work
5. code — implementation

Conflicts must be resolved by updating the **higher-level document**,
not by local code changes.

---

## 7. What Is Explicitly Out of Scope

Agents must not introduce:

* learning from human edits
* hidden persistence
* cross-GSM propagation
* UI-driven backend logic

These are architectural violations unless explicitly approved.

---

## 8. Summary

This document exists to prevent drift across:

* long-running development efforts
* multiple AI-assisted sessions
* multiple contributors

If unsure, stop and escalate via a ticket or documentation update.
