# Ticket #94: Disallow Disease Terms as Tissue Type (Deterministic Unknown + Flag)

## Background

In multiple GEO datasets, the LLM outputs disease names (e.g. *Tumor*, *Lymphoma*, *Cancer*) into the `tissue_type` field.  
This commonly occurs when samples are derived from tumors, hematologic malignancies, or cancer cell lines.

Example (GSE260674, GSM8122220):

- tissue_type: "Lymphoma"
- disease: "Lymphoma" (correctly grounded, terminal DOID)
- cell_line: "OCI-Ly18" (lymphoma-derived)

Here, **tissue_type contains a disease label, not an anatomical structure**.  
Uberon does not contain such concepts, so ontology grounding fails as expected.

Attempting LLM repair is inappropriate because:
- The true anatomical source (blood, lymph node, bone marrow, spleen, in vitro) is ambiguous.
- Cross-sample inference is out of scope.
- Guessing introduces false precision.

This pattern is structurally similar to prior cases such as:
- "Tumor" as tissue_type
- "Cancer" as tissue_type

But is distinct because the disease field is already correctly and terminally resolved.

---

## Problem

The pipeline currently:
- Attempts ontology repair on `tissue_type`
- Leaves disease-derived tissue strings unchanged
- Flags `ontology_low_confidence_tissue_type` without semantic explanation

This obscures the true issue: **disease terms leaking into tissue_type**.

---

## Proposed Policy

### 1. Deterministic Detection

Introduce a deterministic check:

If:
- `tissue_type` string matches a known disease label (DOID / NCIT canonical label or synonym)
- AND the same (or equivalent) disease is already present in the `disease` field

Then classify the tissue value as a **non-anatomical disease placeholder**.

Examples to catch:
- Tumor
- Cancer
- Lymphoma
- Leukemia
- Myeloma
- Carcinoma
- Sarcoma

---

### 2. Deterministic Resolution

When detected:

- Set:
  - `tissue_type = "Unknown"`
- Lock the field with reason:
  - `tissue_type_disease_label_used_as_tissue`
- Do **not** invoke LLM repair
- Do **not** attempt ontology grounding

Disease field remains unchanged.

---

### 3. Flagging (Curator-Facing)

Add a specific flag:

- `tissue_type_disease_label_used_as_tissue`

This flag indicates:
- The submitter or LLM conflated disease identity with anatomical source
- Human curator review is required if anatomical provenance matters

This flag is **not an error**, but a semantic ambiguity marker.

---

## Acceptance Criteria

- Disease terms appearing in `tissue_type` are never passed to Uberon matching.
- `tissue_type` becomes `"Unknown"` deterministically in such cases.
- Disease remains terminal and unchanged.
- No LLM repair attempts are made for this condition.
- Audit log clearly records:
  - original tissue value
  - deterministic override reason
  - explicit curator-facing flag

---

## Non-Goals

- Do not infer anatomical tissue from disease.
- Do not use other GSMs in the same GSE to infer tissue.
- Do not attempt probabilistic or LLM-based guessing.

---

## Rationale

This preserves:
- Ontology correctness
- Per-GSM determinism
- Conservative semantics (no false certainty)
- Clear separation of disease vs anatomical context

And aligns with v0.9’s philosophy:
> *Flag ambiguity instead of hallucinating precision.*

---

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-94.md` and paste this ticket verbatim.
