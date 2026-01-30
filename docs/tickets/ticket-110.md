# Ticket #110: Persistent Override Save/Load per GSE Directory + Export Final 8-Field Annotations

## Background

Today, curator edits are session-only. The UI can export overrides, but curators
must then manually rerun a CLI command to apply them.

This is slow and breaks the curator workflow.

We want:
1) a “Save overrides” action that persists overrides to the GSE directory so the
   UI can restore state on reload, and
2) a true “Export final annotations” action that writes the final 8-field JSONL
   with overrides applied (similar to backend annotations output).

## Problem Statement

Current behavior requires curators to:
- export overrides.jsonl manually,
- then apply it with a separate command line step,
- and the UI does not restore editing state on reload.

Additionally, there is no UI export for the final “curator-applied” 8-field
annotations JSONL for downstream use.

## Proposed Change (UI Only)

### 1) Persistent Overrides: Save + Auto-Load

#### File location (per active GSE)
When a curator clicks **Save overrides**:
- write `overrides.jsonl` into the active GSE directory (the same directory that
  contains `curation.jsonl`), e.g.
  `<GSE_DIR>/overrides.jsonl`

#### Format
Use the existing overrides format already emitted by the UI today (no schema
change). Do not add new keys unless they already exist.

#### Load behavior
On UI load:
- if `<GSE_DIR>/overrides.jsonl` exists, load it automatically and apply it to
  populate the session override state.
- if it does not exist, start with a clean session override state.

#### Safety / guardrails
- The UI must never auto-write files. Disk writes occur only when the curator
  explicitly clicks Save.
- Provide a clear indicator:
  - “Saved overrides detected” (loaded from disk), and
  - “Unsaved edits” (session differs from disk).
- Provide “Revert to saved” and “Discard saved overrides” actions:
  - Revert to saved: reload from `<GSE_DIR>/overrides.jsonl`
  - Discard saved: delete `<GSE_DIR>/overrides.jsonl` (with confirmation)

Multi-GSE mode (Ticket #107):
- overrides are saved/loaded independently per GSE directory.

### 2) Export Final Annotations (8-field JSONL with overrides applied)

Add a separate explicit action: **Export final annotations**.

Behavior:
- Create a JSONL file (default name suggested by UI, e.g. `annotations.final.jsonl`)
  in a user-selected location (Streamlit download or write-to-disk, depending on
  current UI architecture).
- The exported content is a per-GSM JSON object containing exactly the 8 output
  fields:
  `gse_accession`, `gsm_accession`, `data_type`, `organism`, `tissue_type`,
  `cell_line`, `disease`, `treatment`
- Values in the export are:
  - session override value if present, else backend value from `curation.jsonl`
- Do not include flags, evidence, or audit content in this export.

Clarify in UI text:
- “This export applies curator overrides but does not rerun backend validation,
  repair, or ontology grounding.”

### 3) UI Cleanup for Export Section

Replace “Overrides export (session-only edits)” section with two clear panels:

- **Overrides (persistent)**
  - Save overrides
  - Revert to saved
  - Discard saved
  - Status indicators (saved vs unsaved)

- **Exports**
  - Export final annotations (8 fields)

### 4) Documentation Updates (`docs/ui.md`)

Update `docs/ui.md` to document:
- overrides persistence behavior (`<GSE_DIR>/overrides.jsonl`)
- auto-load of saved overrides on startup
- the distinction between:
  - saving overrides (persistent state for UI and later runs)
  - exporting final annotations (downstream consumable output)

## Why No Backend Change Is Required

- Overrides remain explicit curator inputs; the backend is not modified.
- No validation/repair/policy logic is changed.
- The UI is only persisting the same overrides artifact it already exports today,
  and generating a downstream annotations file by applying overrides locally.

## Policy Impact

* [x] No policy change
* [ ] Policy clarification only
* [ ] Policy change

## Acceptance Criteria

1. After edits, clicking “Save overrides” writes `<GSE_DIR>/overrides.jsonl`.
2. Reloading the UI auto-loads `<GSE_DIR>/overrides.jsonl` and restores edits.
3. Multi-GSE mode correctly saves/loads overrides per GSE directory.
4. “Discard saved overrides” removes `<GSE_DIR>/overrides.jsonl` with confirmation.
5. “Export final annotations” produces a JSONL with exactly 8 fields per GSM and
   applies overrides deterministically.
6. UI clearly states that exports do not retrigger backend logic.
7. `docs/ui.md` is updated accordingly.
8. Existing UI tests pass or are updated to reflect persistence/export behavior.

## Non-Goals

- No backend re-run, no re-validation, no ontology re-grounding.
- No learning from overrides.
- No schema changes to curation.jsonl/evidence.jsonl/audit.jsonl.

## Constraints

- File writes must be explicit user actions only (no silent persistence).
- Preserve determinism and auditability.
- Keep per-GSE boundaries strict; do not mix overrides across GSEs.

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-110.md` and paste this ticket verbatim.
