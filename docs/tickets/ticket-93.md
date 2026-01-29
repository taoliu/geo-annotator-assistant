# Ticket #93: Normalize `Healthy, <Genotype/Strain>` Disease Strings to Terminal `Healthy`

## Milestone
v0.9 — Validation, Repair, and Reporting Consolidation

## Type
Policy clarification / deterministic normalization (disease)

## Status
Proposed

---

## Summary

Introduce a deterministic disease normalization rule for **mixed disease strings** that combine an explicit healthy status with **genotype, strain, or model descriptors**, such as:

- `Healthy, Ldlr-/- Leiden mice`
- `Healthy ApoE-/- mice`
- `Normal WT C57BL/6 mice`

These cases should be normalized to the terminal disease value **`Healthy`**, with genotype/model context preserved in audit only.

---

## Motivation

GEO metadata frequently encodes **health status and genetic background in a single disease string**, especially for animal models. These strings are:

- Not valid disease ontology terms
- Not intended to represent pathology
- Guaranteed to fail DOID/NCIT grounding
- Currently trigger unnecessary repair attempts and FLAGGED records

Example observed in v0.9 testing:

```
disease = "Healthy, Ldlr-/- Leiden mice"
```

This is **not a disease**. It explicitly states the sample is healthy.

---

## Policy Definition (Authoritative)

### Healthy + Genotype / Strain Disease Normalization Rule

When **all** of the following conditions hold:

1. Field is `disease`
2. Raw value contains an explicit healthy indicator:
   - `healthy`
   - `normal`
   - `control`
   (case-insensitive)
3. Remaining content consists of **genotype, strain, or model descriptors**, including but not limited to:
   - `-/-`, `+/-`, `KO`, `knockout`, `transgenic`
   - strain names (e.g. `C57BL/6`, `Leiden`)
   - organism indicators (e.g. `mouse`, `mice`, `rat`)
4. The string does **not** contain a known disease name
5. Organism is non-human (or explicitly an animal model)

Then:

- Canonical disease MUST be set to `Healthy`
- Disease field becomes **terminal**
- Ontology grounding MUST be skipped
- LLM repair MUST NOT be triggered
- `ontology_low_confidence_disease` MUST NOT be raised

---

## Canonical vs Audit Behavior

| Aspect | Behavior |
|------|---------|
| `final_output.disease` | `Healthy` |
| Ontology grounding | Skipped |
| Repair attempts | None |
| Audit log | Preserve full original string |
| Final decision | MAY be `ACCEPT` if no other failures |

---

## Flag Semantics

### Optional informational flag
`disease_contains_genotype_context`

Meaning:
> Disease field combined healthy status with genotype or strain information and was normalized to `Healthy`.

Properties:
- Informational only
- Does not trigger repair
- Does not block ACCEPT

(Flag emission optional but recommended for curator transparency.)

---

## Scope

IN SCOPE:
- Disease normalization logic
- Handling of animal model genotype descriptors
- Repair boundary enforcement
- Audit transparency

OUT OF SCOPE:
- Extracting genotype into a new field
- Inferring disease from genotype
- Handling mixed true-disease + genotype strings
- Schema changes
- UI changes

---

## Implementation Notes (Non-Prescriptive)

- Apply normalization **before ontology grounding**
- Use a conservative allowlist of genotype/strain markers
- Ensure rule precedence over ontology and semantic validators
- Preserve raw disease string in audit for traceability

---

## Tests to Add

1. Positive cases:
   - `Healthy, Ldlr-/- Leiden mice` → `Healthy`
   - `Normal ApoE-/- mice` → `Healthy`
   - No ontology attempts, no repair

2. Negative cases:
   - `Familial hypercholesterolemia in Ldlr-/- mice` → rule not applied
   - `Tumor-bearing ApoE-/- mice` → rule not applied
   - `Healthy tissue adjacent to tumor` → rule not applied

---

## Rationale

Health status is explicit and should not be overridden by genotype context.  
Normalizing these strings deterministically improves correctness, reduces noise, and avoids inappropriate ontology or LLM-driven behavior.
