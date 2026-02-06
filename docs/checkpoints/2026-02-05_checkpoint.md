# Checkpoint — 2026-02-05

## Project
**GEO GSM Annotator Agent**

## Checkpoint Purpose
This checkpoint records the authoritative system state at the conclusion of
**Milestone v1.1 (Curator UI & UX Refinement)**.

It is a factual snapshot, not a design proposal.

---

## Milestone Status

- **v1.1 Curator UI & UX Refinement: COMPLETED**
- Previous milestone: v1.0 Curator UI
- Next planned milestone: **v1.2 — CLI ergonomics and command-line options**
  (`geo-gsm-annotate`)

---

## Backend State (Authoritative)

- Backend behavior frozen as of **v0.9**
- Validation, repair, ontology grounding, and reporting logic unchanged
- Output schema unchanged:
  - exactly 8 canonical GSM-level fields
- No new inference, no schema changes, no policy changes

Authoritative backend artifacts remain:
- `curation.jsonl`
- `evidence.jsonl`
- `audit.jsonl`
- override artifacts

---

## UI State (v1.1)

### Table Architecture
- Curation table implemented using **AG Grid**
- Always-on editing (no edit-mode toggle)
- Modal-based inspection removed

### Workflow Columns
- Pinned, icon-based columns:
  1. Status (icon-only)
  2. Checked (persistent curator marker)
  3. Edited (live pencil indicator)
- Workflow columns are non-movable and compact

### Edited Semantics
- Edited indicator updates live
- Reflects:
  - unsaved session edits
  - saved overrides
- Clears correctly on revert and discard operations
- No page refresh required

### Checked Semantics
- Curator-controlled checkbox
- Persisted to disk as a UI-only artifact
- Does not affect backend decisions or exports

---

## Evidence and Diagnostics

- **`evidence.jsonl` is the sole authoritative source** for per-field UI diagnostics
- Cell highlighting rule:
  - highlight **if and only if**
    `evidence_by_field[field].flags` is non-empty
- Fallback states are informational only and not highlighted
- Redundant diagnostic columns removed:
  - review flags
  - terminal fallbacks
  - outliers
  - primary failure
  - flag summary
  - flagged_fields

### Tooltip Inspection
Per-field hover tooltips include (read-only):
- displayed value
- backend-derived value
- LLM raw proposal
- ontology alternates (when present)
- evidence attempts
- ontology status
- terminal fallback
- evidence flags

---

## Curator Workflow Features

- Explicit bulk editing:
  - multi-row selection
  - single-column, single-value apply
  - preview before apply
  - fully reversible
- Progressive disclosure for persistence actions:
  - “Save overrides” always visible
  - “Revert to saved” and “Discard saved overrides” hidden by default
- Session-level edit controls and persistence controls are clearly separated

---

## Export Capabilities

- Per-GSE CSV export:
  - GSE-wide biology summary
  - final annotations (8 canonical fields)
- Aggregate CSV export:
  - all GSMs across all GSEs loaded under `--input-dir`
- All exports:
  - apply saved overrides
  - do not trigger backend reprocessing
  - are deterministic and reporting-ready

---

## Explicit Non-Changes

- No backend logic modifications
- No policy updates
- No ontology updates
- No new flags or failure codes
- No CLI changes in this milestone

---

## Overall Assessment

- UI is production-ready for curator-scale usage
- Evidence transparency and curator trust improved
- System remains fully deterministic and auditable
- Clean handoff point for next milestone focusing on CLI ergonomics

---

**Checkpoint recorded:** 2026-02-05
