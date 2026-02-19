# Ticket #188: GSE Dropdown Shows Flagged/Checked Counts with Color-Blind Friendly Badges

## Background

Curators often need to navigate across many GSEs and quickly find which GSEs need review.
Current UI provides:
- a GSE dropdown
- prev/next buttons

But the dropdown does not expose review workload at-a-glance (FLAGGED burden) or progress (checked).

This ticket adds compact workload/progress indicators next to each GSE accession.

Authoritative UI constraints:
- UI is non-authoritative and must not change backend semantics.
- `curation.jsonl`, `evidence.jsonl`, `audit.jsonl` are read-only inputs.
- Checked state is workflow metadata only. :contentReference[oaicite:3]{index=3}

## Problem Statement

When many GSEs are available, curators must click into each GSE to discover:
- how many samples are FLAGGED (need review)
- how many samples are already checked (review progress)

This increases clicks and time, and makes it easy to miss high-priority GSEs.

## Proposed Change

Enhance the GSE selection UI so each dropdown option displays:

`GSE12345  [50/100]  [20/100]`

Where:
- `[50/100]` = flagged_count / total_count
- `[20/100]` = checked_count / total_count

Visual requirements:
- Both counts are shown as pill badges (ellipse/rounded box).
- Flagged badge uses a color-blind friendly “red” (Okabe-Ito Vermillion: `#D55E00`).
- Checked badge uses a color-blind friendly “green” (Okabe-Ito Bluish Green: `#009E73`).
- Text inside pills should have sufficient contrast (default white text is acceptable if contrast is adequate).

Behavioral requirements:
- Total count = number of GSM rows present for that GSE in loaded `curation.jsonl`.
- Flagged count = count of rows with `final_decision == "FLAGGED"` in `curation.jsonl`.
- Checked count = count of rows marked checked in the existing UI checked-state store for that GSE.
- Counts must update when:
  - checked markers change
  - the loaded dataset changes
- No backend re-run, no flag reinterpretation, no new diagnostics.

Implementation note (Streamlit limitation):
- Native `st.selectbox` options cannot be richly styled per-item.
- Implement a small UI component to render a searchable dropdown with per-option HTML/CSS badges
  (Streamlit components / `st.components.v1`).
- Provide a fallback mode if the component fails to load:
  - show plain text `GSE12345 50/100 20/100` without color pills, still functional.

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

1. **Correct counts**
   - For each GSE in the dropdown, displayed numbers equal:
     - total_count: number of GSMs loaded for that GSE
     - flagged_count: number of GSMs where `final_decision == "FLAGGED"`
     - checked_count: number of GSMs marked checked
2. **No semantics changes**
   - No changes to backend outputs, decision routing, evidence interpretation, or flags.
   - UI uses read-only `curation.jsonl` to compute counts.
3. **Explicit, reversible workflow**
   - Checked markers remain explicit workflow state only.
   - No auto-checking or propagation across GSEs.
4. **Rendering**
   - Dropdown shows two pill badges per option when component loads.
   - Flagged pill uses `#D55E00`, checked pill uses `#009E73`.
   - Pills are ellipse-style with padding and rounded corners.
5. **Fallback**
   - If rich component cannot load, dropdown still works with plain text counts.
6. **Performance**
   - For N GSEs, summary generation is O(total GSMs) once per load, not per-render loop.
   - Switching selection does not trigger expensive recomputation beyond necessary UI state refresh.
7. **Tests**
   - Add/update UI tests validating:
     - correct count computation given a small synthetic curation dataset + checked store
     - formatting string in fallback mode
     - (if feasible) snapshot/DOM test for component output, otherwise unit test the option-model.

## Non-Goals

- Sorting GSEs by workload (can be separate ticket).
- Adding any new flags, diagnostics, or inference.
- Any backend changes.

## Constraints

- Treat `curation.jsonl`, `evidence.jsonl`, `audit.jsonl` as read-only.
- Do not re-run validation or reinterpret evidence flags.
- Do not change how FLAGGED is defined (use existing `final_decision` only).
- Do not introduce cross-GSM propagation.

## Guiding Principle

UI increases curator productivity without becoming a new source of truth.

## Ticket File Requirement (MANDATORY)

Create `docs/tickets/ticket-188.md` and paste this ticket verbatim.
