# AGENTS.md — Development Governance and Agent Roles

This document defines **how human developers, ChatGPT, and Codex CLI collaborate**
on the GEO GSM Annotator Agent project.

It is a governance document, not an implementation guide.

---

## 1. Roles and Responsibilities

### ChatGPT (Architect / Reviewer)

ChatGPT acts as:

- system architect
- design reviewer
- ticket author
- documentation editor

Responsibilities:

- Define architectural intent and invariants
- Propose milestone plans and tickets
- Ensure determinism, auditability, and schema stability
- Review designs for unintended semantic changes
- Update whitepaper, milestones, checkpoints, and handoff docs
- Maintain `docs/policies/policy-spec.md` as the authoritative backend policy spec

ChatGPT **does not**:

- implement production code
- bypass ticketing
- silently change system semantics

---

### Codex CLI (Implementer)

Codex CLI acts as:

- code implementer
- test author
- refactor executor

Responsibilities:

- Implement tickets verbatim
- Preserve architectural invariants
- Add or update tests as required by tickets
- Save tickets and changes as markdown artifacts

Codex CLI **must not**:

- introduce behavior not specified in a ticket
- redesign pipeline structure
- modify output schema
- remove audit signals

---

## 2. Architectural Invariants (Non-Negotiable)

All agents must respect the following invariants:

- Exactly **8 output fields** per GSM
- Deterministic decision routing
- Bounded repair loops
- Read-only, non-decisional RAG
- Fully auditable execution

Any change violating these invariants requires explicit approval
and a whitepaper update.

---

## 3. Ontology and RAG Governance (v0.6+)

### Deterministic-first retrieval

- Ontology retrieval must prioritize deterministic exact matches
- Vector similarity search is **fallback-only**
- Exact matches must short-circuit embedding and vector queries

### Terminal exact semantics

A terminal exact match is defined as:

- `status == MATCHED`
- `score == 1.0`
- exact match type (label, normalized label, synonym, or ID)

Terminal exact matches:

- may canonicalize output labels
- may lock fields against later repair
- must be auditable and config-gated

Agents must not bypass or weaken these semantics.

---

## 4. Embedding and Retrieval Implementation Notes

- ChromaDB collections may attach an embedding function when required
- Embedding device (`cpu`, `cuda`, `mps`) must respect configuration
- Avoid unnecessary embedding calls whenever behavior can be preserved

Older guidance that prohibited embedding functions in Chroma is
superseded by ticketed v0.6 decisions.

---

## 5. Ticket-Driven Development Model

- All changes must be associated with a numbered ticket
- Tickets define:
  - scope
  - constraints
  - acceptance criteria
  - required tests
- Code changes without tickets are invalid

Tickets are stored under `docs/tickets/` and are the
**only permitted mechanism** for altering code behavior.

### Policy-aware tickets

If a ticket changes validation, repair, fallback, flags, or audit semantics,
the agent must:

1. Read `docs/policies/policy-spec.md` first
2. Update it in the same ticket if behavior is new or modified

### Testing requirement

Unless a ticket explicitly says otherwise, Codex must run unit tests with:

`uv run pytest -q`

If tests fail, fix them within the same ticket scope before reporting completion.

---

## 6. UI Governance and Authority Boundaries (v1.0+, clarified in v1.1)

The curator UI is **non-authoritative**.

It must never change backend semantics, inference, or policy behavior.

### Authoritative inputs for UI

- `curation.jsonl` — backend decisions and final annotations
- `evidence.jsonl` — **sole authoritative source for per-field diagnostics**
- `audit.jsonl` — execution trace and decision audit

UI code must treat these artifacts as **read-only inputs**.

---

### UI permissions (allowed)

The UI may:

- Display backend outputs and evidence verbatim
- Persist **explicit curator overrides** (`overrides.jsonl`)
- Persist **UI-only workflow markers**, including:
  - curator “checked” status
- Support bulk editing as an explicit, reversible UI operation
- Export final annotations (with overrides applied) in reporting formats

All persistence must be:
- user-triggered
- explicit
- auditable
- non-inferential

---

### UI prohibitions (non-negotiable)

The UI must **not**:

- re-run backend validation, repair, or ontology grounding
- reinterpret backend flags or ontology confidence
- synthesize new diagnostic signals
- infer correctness from patterns across GSMs
- propagate values across GSMs implicitly
- introduce learning from curator edits
- reintroduce modal-driven inspection as a primary interaction model

If a UI feature appears to require backend behavior changes,
**stop immediately and raise a backend ticket**.

---

### UI diagnostic rules (v1.1 invariant)

- Per-field diagnostics shown in the UI must come **only from `evidence.jsonl`**
- Cell highlighting is permitted **if and only if**
  `evidence_by_field[field].flags` is non-empty
- Fallback states (`ontology_status == FALLBACK`) are informational only
- Diagnostic summary columns (primary failure, flag summary, etc.)
  must not be reintroduced without explicit approval

---

## 7. Documentation Hierarchy (Authority Order)

Agents must respect the following order of authority:

1. `docs/whitepaper.md` — architectural law
2. `docs/policies/policy-spec.md` — validation / repair / reporting semantics
3. `docs/milestones/v*.md` — completed milestone scope
4. `docs/checkpoints/yyyy-mm-dd_checkpoint.md` — system handoff anchors
5. `docs/RESUME.md` — concise one-page project snapshot (non-authoritative)
6. `docs/tickets/ticket-xx.md` — permitted work
7. code — implementation

Conflicts must be resolved by updating the **higher-level document**,
not by local code changes.

---

## 8. What Is Explicitly Out of Scope

Agents must not introduce:

- learning from human edits
- hidden or implicit persistence
- cross-GSM propagation
- UI-driven backend logic
- silent schema drift

These are architectural violations unless explicitly approved.

---

## 9. Summary

This document exists to prevent drift across:

- long-running development efforts
- multiple AI-assisted sessions
- multiple contributors
- UI and backend evolution

When in doubt, stop and escalate via:
- a ticket
- a milestone note
- or a documentation update
