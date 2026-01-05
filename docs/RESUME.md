# How to Resume This Project

This document explains how to correctly resume work on the **geo-gsm-annotator-agent** project in a new session (human or AI-assisted).

Follow these steps **in order**.

---

## 1. Read the architectural contract (MANDATORY)

Start with:

- `docs/whitepaper.md`

This document defines:
- architectural invariants,
- validation and repair philosophy,
- evidence-first rules,
- configuration governance.

Do **not** propose changes that violate the whitepaper without opening a new milestone.

---

## 2. Identify the current development phase

Read, in order:

1. The latest file in `docs/milestones/`
2. The latest file in `docs/checkpoints/`

As of **2026-01-04**:
- Milestone **v0.2 (Ontology grounding and evidence-first repair)** is complete.
- The system is mechanically correct and stable.
- The next planned work is semantic/policy refinement (v0.3).

---

## 3. Check repository state

- Inspect the latest git tag.
- Confirm no uncommitted changes affect core logic.
- Review `docs/tickets/` to see recently completed tickets.

Active development must always be ticket-driven.

---

## 4. Ontology grounding setup (REQUIRED FOR RUNNING)

Ontology grounding depends on a prebuilt, external ChromaDB.

To enable it:

1. Place the directory `ontology_chroma_db/` next to the repository root.

2. The directory **must** contain: `chroma.sqlite3`

3. In your config file, ensure ontology grounding is enabled under the canonical namespace: `rag.ontology.*`

---

## 5. Ontology retrieval invariants (IMPORTANT)

Ontology retrieval follows strict rules:

- Query embeddings are computed explicitly via `embed_query`.
- Use:
```python
get_collection(name=...)
```

**without** passing an embedding function.

* This avoids conflicts with persisted embeddings in ChromaDB.

This behavior intentionally mirrors the external `rag_ontologies` pipeline.

Embedding model requirements:

* Model: `BAAI/bge-base-en-v1.5`
* Embeddings must be normalized.

---

## 6. Testing environment (MANDATORY)

All tests must be run using the project’s `uv` environment:

```bash
uv run pytest -q
```

Do not run `pytest` directly.

If configuration, validation, or decision routing logic is modified:

* add or update tests accordingly.

---

## 7. Development workflow summary

To resume development safely:

1. Understand the **architecture** (whitepaper).
2. Confirm the **current milestone scope**.
3. Write or pick a **ticket** under `docs/tickets/`.
4. Implement **only what the ticket specifies**.
5. Run tests under `uv`.
6. Update checkpoints or milestones if scope is completed.

---

## 8. Current recommended next step

The next milestone (v0.3) should focus on:

* Canonical handling of missing or absent information (`Unknown` vs explicit values).
* Field-specific evidence policies.
* Consistent skip/fallback semantics for ontology grounding.

This work is **policy-level**, not mechanical.

---

## Final note

If you are an AI coding agent or chatbot:

* Read `AGENTS.md` before touching code.
* Follow ticket instructions exactly.
* Prefer deterministic, minimal changes over “helpful” refactors.

This project prioritizes correctness, auditability, and long-term consistency.

