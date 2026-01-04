# Tickets — Development Workflow

All development work in this repository is driven by numbered tickets.

This directory contains the authoritative record of **what work was done and why**.

---

## 1. Ticket naming and location (MANDATORY)

Each ticket must be stored as a Markdown file under:

```
docs/tickets/ticket-XXX.md
```

Where:
- `XXX` is the ticket number (e.g. `17`, `17b`, `18`).
- The filename must exactly match the ticket number.

No code change is considered valid unless it is covered by a ticket in this directory.

---

## 2. Ticket content requirements

Each ticket file must include:

1. **Title**
   - Format: `Ticket #XXX: AGENT-WS-XXX — <short description>`

2. **Context**
   - Why the change is needed.

3. **Goal**
   - What the ticket intends to accomplish.

4. **Non-goals**
   - What the ticket explicitly does not change.

5. **Tasks**
   - Concrete, file-level instructions.

6. **Acceptance criteria**
   - How completion is verified.

---

## 3. Ticket-first rule

- Tickets must be written **before** implementation.
- AI coding agents (Codex) must implement **only** what is described in the active ticket.
- “Helpful” extra changes are not allowed unless requested.

---

## 4. Testing requirement

Before a ticket is considered complete, tests must pass under the project environment:

```
uv run pytest -q
```

If a ticket modifies configuration, parsing, or routing logic, tests must be added or updated accordingly.

---

## 5. Relationship to other documents

Priority order for instructions:

1. `docs/whitepaper.md`
2. Milestone documents under `docs/milestones/`
3. This README
4. Individual ticket files

If instructions conflict, follow the higher-priority document.

---

## 6. Scope discipline

- Tickets represent **short-term, concrete work**.
- Architectural changes must be justified at the milestone or whitepaper level.
- Do not overload a ticket with unrelated improvements.

---

This structure exists to keep development consistent across multiple AI-assisted sessions.

