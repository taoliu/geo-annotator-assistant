# Ticket #177: Render composite ontology matches in tooltip (tissue_type)

## Background

After Ticket #176, tissue_type may resolve via composite logic using the
`all_components_required_v1` rule.

In such cases, audit.jsonl contains:

- status = MATCHED
- matched_via = "composite_all_components_required"
- matched_term_id = null
- matched_label = joined canonical string (e.g. "colon & rectum")
- composite_resolution.fragment_matches = detailed per-component matches

The current web UI tooltip assumes a single matched_term_id and alternates list.
As a result, composite MATCHED cases do not display ontology details correctly.

Backend behavior is correct. UI must adapt to new composite semantics.

Scope: Web UI only. No backend changes.

---

## Problem Statement

For composite MATCHED cases:

- `matched_term_id` is null by design (because the ontology match is a set)
- The ontology details exist in `composite_resolution.fragment_matches`
- Tooltip currently renders nothing or incomplete information

This causes inconsistency with how other ontology matches are displayed.

---

## Required Change

Update ontology tooltip rendering logic to support composite matches.

### Trigger Condition

If:

```

matched_via == "composite_all_components_required"

```

Then treat this as a composite MATCHED case.

Do NOT infer composite from matched_term_id being null.
Always rely on `matched_via`.

---

## Rendering Behavior

For composite MATCHED cases:

### Ontology Status Section

Display:

- Ontology status: MATCHED
- Selection rule: all_components_required_v1

### Matched Components Section

Render:

```

Matched components (m/k):
• <label> (<term_id>)
• <label> (<term_id>)

```

Where:
- m = matched_components
- k = total_components
- labels and term_ids come from `composite_resolution.fragment_matches`

Each fragment entry should display:
- canonical label
- term_id
- source (optional, consistent with existing tooltip style)

Do not display alternates list (composite resolution already terminal exact).

---

## Non-Composite Behavior (Must Remain Unchanged)

If `matched_via` is not `"composite_all_components_required"`:

- Preserve existing tooltip rendering logic:
  - Show matched_term_id
  - Show matched_label
  - Show alternates (if any)
  - Show confidence and match_type

No regression allowed.

---

## Constraints

- No backend modification.
- No schema modification.
- No changes to curation.jsonl structure.
- No changes to evidence.jsonl structure.
- Do not fabricate a synthetic matched_term_id for composite matches.
- Deterministic rendering only based on audit.jsonl content.

---

## Acceptance Criteria

Using GSM5585963 (GSE184398):

1. Tooltip displays:

   Matched components (2/2):
   • colon (UBERON:0001155)
   • rectum (UBERON:0001052)

2. Ontology status displays MATCHED.
3. Selection rule displays "all_components_required_v1".
4. No alternates section shown for composite MATCHED.
5. Single-term MATCHED cases render exactly as before (regression check).
6. LOW_CONFIDENCE composite partial cases (future scenario) render:
   - Ontology status: LOW_CONFIDENCE
   - Matched components (m/k)
   - Primary failure displayed correctly.

---

## Implementation Notes (Streamlit + AG-Grid)

Pseudo logic for tooltip renderer:

```

match = ontology_matches[field]

if match.matched_via == "composite_all_components_required":
cr = match.composite_resolution
render_status(match.status)
render_selection_rule(cr.selection_rule)
render_matched_components(cr.fragment_matches,
cr.matched_components,
cr.total_components)
else:
render_single_term(match)

```

No other UI logic should change.

---

## Non-Goals

- No redesign of tooltip layout.
- No support for composite in other fields.
- No ontology UI enhancements beyond composite rendering.
- No visual style changes unrelated to composite handling.

---

## Guiding Principle

Backend defines ontology truth.
UI must faithfully project backend state without reinterpretation.

Create file:
docs/tickets/ticket-177.md

Paste this ticket verbatim.
