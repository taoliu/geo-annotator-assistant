# AGENTS.md — Working Agreement for AI Coding Agents (Codex CLI)

This repository is developed by a small loop of:
1) a human architect (project owner),
2) a chatbot architect (ticket writer / reviewer),
3) an AI coding agent (Codex CLI) that implements tickets.

This file defines how the AI coding agent should work in this repo.

---

## 1. Read these files first (MANDATORY)

Before starting any work, read:

- `docs/whitepaper.md` (architecture + invariants)
- `docs/milestones/` (current milestone scope)
- `docs/tickets/README.md` and the active ticket under `docs/tickets/`
- `config/example_config.yaml` (canonical config schema)

If any instruction conflicts, prioritize in this order:
1) `docs/whitepaper.md`
2) milestone document
3) ticket document
4) code comments

---

## 2. Ticket-first workflow (MANDATORY)

All changes must be driven by a ticket.

For the current ticket:
- implement exactly what is written
- do not add “extra improvements” unless the ticket requests them

After completing the ticket, the AI coding agent must:
- ensure the ticket exists as a file under `docs/tickets/`
  - `docs/tickets/ticket-XXX.md`

---

## 3. Output contract (MANDATORY)

The agent output schema is fixed at 8 fields:

- `gse_accession`
- `gsm_accession`
- `data_type`
- `organism`
- `tissue_type`
- `cell_line`
- `disease`
- `treatment`

Do not add, remove, rename, or restructure these fields.

---

## 4. Configuration contract (MANDATORY)

Retrieval/grounding configuration must live under:

- `rag.*`
- `rag.ontology.*`

Do not introduce new top-level config blocks for retrieval or grounding.

If a config schema change is required, update all of:
- `src/agent/config.py`
- `config/example_config.yaml`
- `config/gat-llama3-3b-it_config.yaml`
- a config-loading unit test

---

## 5. Ontology grounding (IMPORTANT)

The ontology ChromaDB is externally built and read-only.

Query pattern requirement:
- open collection without embedding function
- embed queries explicitly
- query with `query_embeddings=[...]`

Do not pass `embedding_function=` into `get_collection(...)` for the persisted DB.

---

## 6. Testing and quality gates (MANDATORY)

Testing should be run under `uv` environment. Before marking a ticket complete:

- run unit tests:
  - `uv run pytest -q`

- if you change config parsing, add/adjust tests accordingly

- keep logs and audit outputs bounded (no huge dumps)

---

## 7. Minimal diffs and clean commits

- Make the smallest changes needed for the ticket.
- Keep edits localized.
- Avoid reformatting unrelated code.
- Do not rename large modules unless requested.

---

## 8. When uncertain

If there is ambiguity:
- prefer the existing structure in the repository
- follow `docs/whitepaper.md` invariants
- do not invent new conventions

If required, ask the architect for clarification before proceeding.

---
