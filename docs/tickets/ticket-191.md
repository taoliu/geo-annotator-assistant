# Ticket #191: Remove AG Grid Selection Checkbox Column and Keep Checked Column as Sole Row-Completion Indicator

## Background

In the curation table, AG Grid currently renders an additional built-in row-selection checkbox column (with header checkbox) used for multi-selection. Curators already have multi-row selection by clicking rows directly, and the UI already has a dedicated `checked` column that represents completed review workflow state.

The extra AG Grid selection checkbox column is visually redundant and creates confusion with the existing `checked` column.

## Problem Statement

Two checkbox-like mechanisms are visible in the table:

1. AG Grid selection checkbox column for row selection
2. Existing `checked` column for curator workflow completion

This duplicates interaction affordances and makes it unclear which checkbox represents actual checked/completed state.

## Proposed Change

Update AG Grid selection configuration so that:

1. Built-in AG Grid row-selection checkboxes are disabled (including header checkbox).
2. Multi-row selection remains enabled via row click behavior (existing bulk-edit selection workflow).
3. The existing `checked` column remains the only visible checkbox column intended for review completion state and persistence.

No backend semantics change. No change to checked-state persistence format.

## Layer Affected

- [ ] Canonicalization
- [ ] Ontology grounding
- [ ] Validation / Repair
- [ ] Decision routing
- [x] UI only
- [ ] Documentation only

## Policy Impact

- [x] No policy change
- [ ] Policy clarification only
- [ ] Policy change (policy-spec.md must be updated)

## Acceptance Criteria

1. The AG Grid selection checkbox column is no longer rendered.
2. Row click still supports multi-selection for bulk edit workflows.
3. The existing `checked` column remains visible and functional for checked state.
4. Checked persistence to `checked.jsonl` remains unchanged.
5. Tests cover updated AG Grid row-selection options.

## Non-Goals

- Replacing checked-state storage format.
- Changing bulk-edit semantics.
- Reordering unrelated table columns.

## Constraints

- UI remains non-authoritative.
- No backend file/schema changes.
- Keep existing checked-state meaning and persistence.

## Guiding Principle

Use one clear checkbox mechanism for workflow completion while keeping selection mechanics unobtrusive and consistent.

## Ticket File Requirement (MANDATORY)

Create `docs/tickets/ticket-191.md` and paste this ticket verbatim.
