# Ticket #189: Distinguish Blocking vs Advisory Signals in Cell Styling (Outliers + Non-blocking Consistency)

## Background

Curators currently see the same cell background styling for:
1) fields that are truly blocking (caused or contributed to a FLAGGED decision), and
2) fields that are only advisory (example: `gse_outlier_<field>`), even when a record is ACCEPT or when a FLAGGED record has both kinds of signals.

This causes confusion and slows review because advisory “heads-up” signals look like mandatory corrections.

UI governance constraints:
- UI is non-authoritative.
- UI must not re-run validation, reinterpret flags, or synthesize diagnostics.
- UI must consume `curation.jsonl`, `evidence.jsonl`, `audit.jsonl` as read-only inputs.
- Highlighting must follow evidence-first rules and existing backend outputs. :contentReference[oaicite:0]{index=0} :contentReference[oaicite:1]{index=1}

## Problem Statement

The UI cannot currently distinguish:
- **blocking** signals (part of backend decision routing / unresolved failures), vs
- **advisory** signals (GSE-level outliers, explicitly non-blocking consistency flags)

As a result, cells related to `gse_outlier_disease` or other advisory markers appear identical to cells responsible for a FLAGGED decision.

## Proposed Change

Introduce two separate, explicit UI severities for diagnostics styling:

### A) Blocking Severity (existing “error” visual)
A field is styled as **blocking** only if it is implicated by backend routing metadata for that GSM.

Compute `blocking_fields` per GSM using only backend-emitted artifacts (no inference), in the following order:

1. If `rationale.primary_failure` is present and maps to a field:
   - Mark that field blocking.
2. Add any fields present as keys in:
   - `validation.ontology_failures`
   - `validation.semantic_errors`
3. Add any fields referenced in:
   - `validation.format_error_details[*].field`

Blocking styling:
- Keep existing “blocking” styling (current orange background for flagged-causing fields).
- This styling must be applied ONLY to fields in `blocking_fields`.

### B) Advisory Severity (new “info” visual)
A field is styled as **advisory** if it has an explicitly advisory signal emitted by backend artifacts.

Advisory signals:
1. Any flag matching prefix: `gse_outlier_`
   - Example: `gse_outlier_disease` implies advisory on field `disease`.
2. Any explicitly non-blocking consistency flag:
   - `healthy_disease_conflict` (informational-only by policy)

Advisory styling:
- Must be visually distinct from blocking.
- Must NOT reuse the blocking background color.
- Recommended style: thin left border + small “info” icon/badge.
- Use color-blind friendly blue (Okabe–Ito Blue: `#0072B2`) for the advisory accent.

### C) Combined Case (field is both blocking and advisory)
If a field is both blocking and advisory:
- Render blocking as dominant (existing orange background).
- Add the advisory icon/badge as a secondary marker.

### D) Overrides
Overrides remain as the existing override styling (green background).
If a field is overridden and also blocking/advisory:
- Keep override fill (green) as dominant,
- show small icons/badges for blocking/advisory if applicable,
- do not blend fills.

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

1. **Blocking field detection**
   - For each GSM, UI computes `blocking_fields` using only:
     - `rationale.primary_failure`
     - `validation.ontology_failures`
     - `validation.semantic_errors`
     - `validation.format_error_details`
   - UI must not infer blocking from other signals (scores, match types, or text heuristics).

2. **Blocking styling scope**
   - The blocking (orange background) style is applied only to fields in `blocking_fields`.
   - Advisory-only fields must never receive the blocking background.

3. **Advisory detection**
   - `gse_outlier_<field>` is rendered as advisory on `<field>`.
   - `healthy_disease_conflict` is rendered as advisory (non-blocking).
   - No other flags are treated as advisory unless explicitly added by prefix or explicit allowlist.

4. **Advisory styling**
   - Advisory style is distinct from blocking and override styling.
   - Uses color-blind friendly blue accent (`#0072B2`) and non-fill dominant treatment (border/icon).

5. **Combined cases**
   - If both blocking and advisory apply to a field:
     - blocking fill remains dominant,
     - advisory icon/badge is also visible.

6. **Overrides precedence**
   - Override fill (green) remains dominant.
   - Blocking/advisory displayed via icon/badge only when overridden.

7. **No backend changes**
   - No modifications to backend code, artifacts, schema, or semantics.
   - UI remains read-only with respect to `curation.jsonl`, `evidence.jsonl`, `audit.jsonl`.

8. **Tests**
   - Add UI unit tests for:
     - FLAGGED GSM with blocking failure on field A and advisory outlier on field B:
       - A is blocking-styled, B is advisory-styled.
     - FLAGGED GSM with both blocking + advisory on same field:
       - blocking + advisory marker both appear.
     - ACCEPT GSM with advisory outlier:
       - advisory style appears, no blocking style appears.
     - Override + advisory/blocking:
       - override fill dominates, marker icons show.

## Non-Goals

- Changing backend routing, flags, or audit semantics.
- Creating a comprehensive manual “blocking vs non-blocking flags” registry in UI.
- Sorting or triaging rules (separate tickets).

## Constraints

- UI must not re-run validation or grounding.
- UI must not reinterpret backend confidence or scores.
- UI must rely only on explicit backend-emitted routing metadata and explicit advisory prefixes/allowlist.
- All visuals must remain accessible and color-blind friendly.

## Guiding Principle

UI may improve clarity of backend outputs, but must not become a new decision engine.

## Ticket File Requirement (MANDATORY)

Create `docs/tickets/ticket-189.md` and paste this ticket verbatim.
