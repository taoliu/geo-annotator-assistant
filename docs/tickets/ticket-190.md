# Ticket #190: Remove AG Grid Deprecation Warnings and DataFrame Fragmentation Warnings in Curation UI

## Background

During Playwright review of the curation UI launched through `ui.cli` with `--input-dir out/artnet`, two recurring runtime warnings were observed:

1. AG Grid configuration deprecation warnings in browser console:
   - `suppressRowClickSelection` deprecated
   - string `rowSelection` mode deprecated
   - `rowMultiSelectWithClick` deprecated
2. pandas `PerformanceWarning` in Streamlit server logs from repeated column insertion in `_append_aggrid_meta_columns`.

These warnings do not currently break behavior, but they introduce noise, obscure true issues, and create avoidable performance overhead during rerenders.

## Problem Statement

The UI currently uses deprecated AG Grid option keys and repeatedly inserts many columns into a DataFrame in a way that triggers fragmentation warnings. This degrades maintainability and may impact runtime performance for larger datasets.

## Proposed Change

Update curation UI internals without changing semantics:

1. Replace deprecated AG Grid selection options with current object-style `rowSelection` configuration:
   - keep multi-row selection behavior
   - keep click-to-select behavior
   - keep multi-select without modifier keys behavior
2. Refactor `_append_aggrid_meta_columns` to construct metadata columns in a single batch and append them at once, avoiding repeated per-column DataFrame insertion.
3. Add/adjust UI unit tests to verify:
   - grid options do not include deprecated keys and include object-style `rowSelection`
   - meta column append path does not emit pandas fragmentation performance warnings
   - existing blocking/advisory/override behavior remains intact

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

1. **AG Grid deprecations removed**
   - Grid options no longer set deprecated keys:
     - `suppressRowClickSelection`
     - `rowMultiSelectWithClick`
     - string-valued `rowSelection`
   - Grid keeps equivalent user behavior for row selection.
2. **No DataFrame fragmentation warning in meta-column append path**
   - `_append_aggrid_meta_columns` no longer triggers pandas `PerformanceWarning` caused by repeated column insertion.
3. **No UI semantic change**
   - Blocking/advisory/override highlighting behavior is unchanged.
   - Existing UI-only authority boundaries remain unchanged.
4. **Tests**
   - Unit tests cover updated grid option schema and no-fragmentation warning behavior.
   - Existing related UI tests pass.

## Non-Goals

- Any backend behavior or schema changes.
- Any change to diagnostics semantics (blocking vs advisory logic).
- Any redesign of table layout, filters, or curator workflow.

## Constraints

- UI must remain non-authoritative and read-only over backend artifacts.
- Do not re-run backend validation or reinterpret diagnostics.
- Keep current UX behavior while modernizing internals and reducing warnings.

## Guiding Principle

UI stability and maintainability improvements are valid when they preserve existing semantics and curator behavior.

## Ticket File Requirement (MANDATORY)

Create `docs/tickets/ticket-190.md` and paste this ticket verbatim.
