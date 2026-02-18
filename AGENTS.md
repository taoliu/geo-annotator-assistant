# AGENTS.md — Development Governance and Agent Roles

This document defines **how human developers, ChatGPT, and Codex CLI collaborate**
on the GEO GSM Annotator Agent project.

It is a governance document, not an implementation guide.

---

## 1. Roles and Responsibilities

### ChatGPT (Architect / Reviewer)

ChatGPT acts as:

* system architect
* design reviewer
* ticket author
* documentation editor
* investigation orchestrator

Responsibilities:

* Define architectural intent and invariants
* Propose milestone plans and tickets
* Ensure determinism, auditability, and schema stability
* Review designs for unintended semantic changes
* Update whitepaper, milestones, checkpoints, and handoff docs
* Maintain `docs/policies/policy-spec.md` as the authoritative backend policy spec
* When necessary, request **read-only Codex investigation tasks** to trace behavior in the codebase

ChatGPT **does not**:

* implement production code
* bypass ticketing
* silently change system semantics
* modify code outside ticket scope

---

### Codex CLI (Implementer)

Codex CLI acts as:

* code implementer
* test author
* refactor executor
* read-only investigator (when instructed)

Responsibilities:

* Implement tickets verbatim
* Preserve architectural invariants
* Add or update tests as required by tickets
* Save tickets and changes as markdown artifacts
* When instructed, perform read-only investigations and report:

  * file paths
  * function names
  * decision paths
  * rule origins

Codex CLI **must not**:

* introduce behavior not specified in a ticket
* redesign pipeline structure
* modify output schema
* remove audit signals
* silently change semantics

---

## 2. Architectural Invariants (Non-Negotiable)

All agents must respect the following invariants:

* Exactly **8 output fields** per GSM
* Deterministic pipeline ordering
* Deterministic decision routing
* Bounded repair loops
* Read-only, non-decisional RAG
* Canonicalization precedes ontology grounding
* Structured context overrides free text
* Fully auditable execution

Any change violating these invariants requires explicit approval
and a whitepaper update.

---

## 3. Ontology and RAG Governance

### Deterministic-first retrieval

* Ontology retrieval must prioritize deterministic exact matches
* Synonym parsing must be consistent across all ontology sources
* Vector similarity search is fallback-only
* Exact matches must short-circuit embedding and vector queries

### Terminal exact semantics

A terminal exact match is defined as:

* `status == MATCHED`
* `score == 1.0`
* exact match type (label, normalized label, synonym, or ID)

Terminal exact matches:

* may canonicalize output labels
* may lock fields against later repair
* must be auditable

Agents must not bypass or weaken these semantics.

---

## 4. Deterministic Canonicalization Layer (v1.4+)

The canonicalization layer precedes ontology grounding.

It includes:

* Placeholder normalization (`"Not Available"` → `"Unknown"`)
* Healthy normalization (`"NA (Healthy Donors)"` → `"Healthy"`)
* Deterministic disease rewrites (e.g., mesothelioma mapping)
* Deterministic tissue rewrites (e.g., `"peripheral blood"` → `"blood"`)
* Composite field resolution

Canonicalization must:

* be deterministic
* be policy-defined
* be auditable
* not rely on LLM repair

---

## 5. Ticket-Driven Development Model

* All changes must be associated with a numbered ticket
* Tickets define:

  * scope
  * constraints
  * acceptance criteria
  * required tests

Code changes without tickets are invalid.

Tickets are stored under `docs/tickets/` and are the
**only permitted mechanism** for altering code behavior.

---

### Policy-aware tickets

If a ticket changes validation, repair, fallback, flags, or audit semantics,
the agent must:

1. Read `docs/policies/policy-spec.md` first
2. Update it in the same ticket if behavior is new or modified

---

### Testing requirement

Unless a ticket explicitly says otherwise, Codex must run unit tests with:

```
uv run pytest -q
```

If tests fail, they must be fixed within the same ticket scope before completion.

---

## 6. Codex-Assisted Investigation Workflow (v1.4)

The architect may issue read-only investigation tasks to Codex in order to:

* Trace where a failure code is emitted
* Identify decision escalation paths
* Locate normalization logic
* Confirm invariant compliance
* Diagnose unexpected flags

Rules:

* Investigation tasks are read-only unless explicitly authorized otherwise
* Reports must cite file paths and functions
* Reports must describe trigger conditions clearly
* No behavior changes are allowed during investigation

Investigation supports architecture.
It does not replace ticket workflow.

---

## 7. UI Governance and Authority Boundaries

The curator UI is **non-authoritative**.

It must never change backend semantics, inference, or policy behavior.

### Authoritative inputs for UI

* `curation.jsonl` — backend decisions and final annotations
* `evidence.jsonl` — sole authoritative source for per-field diagnostics
* `audit.jsonl` — execution trace

UI code must treat these artifacts as read-only inputs.

---

### UI permissions (allowed)

The UI may:

* Display backend outputs and evidence verbatim
* Persist explicit curator overrides (`overrides.jsonl`)
* Persist workflow markers (e.g., checked status)
* Support bulk editing as explicit, reversible UI operations
* Export final annotations

All persistence must be:

* user-triggered
* explicit
* auditable
* non-inferential

---

### UI prohibitions (non-negotiable)

The UI must not:

* re-run backend validation or ontology grounding
* reinterpret backend flags
* synthesize new diagnostics
* propagate values across GSMs
* infer patterns across GSMs
* learn from curator edits
* alter schema

If a UI feature requires backend logic changes,
stop and raise a backend ticket.

---

## 8. Documentation Hierarchy (Authority Order)

Agents must respect the following order of authority:

1. `docs/whitepaper.md` — architectural law
2. `docs/policies/policy-spec.md` — validation / repair / reporting semantics
3. `docs/milestones/v*.md` — completed milestone scope
4. `docs/checkpoints/yyyy-mm-dd_checkpoint.md` — system handoff anchors
5. `docs/RESUME.md` — concise project snapshot (non-authoritative)
6. `docs/tickets/ticket-xx.md` — permitted work
7. code — implementation

Conflicts must be resolved by updating the higher-level document,
not by local code changes.

---

## 9. What Is Explicitly Out of Scope

Agents must not introduce:

* learning from human edits
* hidden or implicit persistence
* cross-GSM propagation
* UI-driven backend logic
* silent schema drift
* non-deterministic repair behavior

These are architectural violations unless explicitly approved.

---

## 10. Summary

This document prevents semantic drift across:

* long-running development efforts
* multiple AI-assisted sessions
* multiple contributors
* UI and backend evolution

When in doubt:

* stop
* investigate
* open a ticket
* update documentation

Determinism, auditability, and invariant preservation always take priority.
