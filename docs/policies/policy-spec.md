# Policy Spec (v0.9)

## 1. Overview
This document describes **current behavior** of the GEO GSM Annotator Agent as implemented in code. **Code is authoritative**; this document is descriptive and must not be used to infer future behavior.

## 2. Pipeline Stages and Precedence
Execution order (see `src/agent/run_single.py`, `src/agent/repair_loop.py`):
1. **LLM raw output** (prompt `prompts/label_v1.txt`) → parse and normalize to 8 required fields.
2. **Format validation** (`src/validator/format_validator.py`) against required keys and word limits. Includes JSON extraction and truncated treatment salvage.
   Format errors are routed at record level via `validation.format_errors`; audit-level per-field attribution is emitted in `validation.format_error_details`.
3. **Semantic validation** (`src/validator/semantic_validator.py`) for field-level plausibility.
4. **Ontology grounding** (`src/validator/ontology_validator.py` + grounders) for `data_type`, `tissue_type`, `cell_line`, `disease`.
5. **Consistency validation** (`src/validator/consistency_validator.py`) for cross-field/context conflicts.
6. **Deterministic canonicalization & locks** (`src/agent/ontology_canonicalization.py`).
7. **Decision routing & repair loop** (`src/validator/decision_engine.py`, `spec/decision_table.yaml`, `src/agent/repair_loop.py`).
8. **Terminal fallback enforcement** (repair loop + locked fields).
9. **Final decision**: ACCEPT / FLAGGED / REJECT (see Section 9).

Precedence rules:
- Failures are consolidated per field; **primary failure** is selected deterministically (`src/validator/failure_codes.py`).
- Evidence-first failures (`disease_inferred_without_evidence`, `cell_line_inferred_without_evidence`, `tissue_type_is_cell_type`) are prioritized across fields.
- **Locked fields** override later repairs and final output assembly (`src/agent/run_single.py`).

## 3. Field-by-Field Policy Rules
All fields are strings. The output schema always includes exactly 8 fields:
`gse_accession`, `gsm_accession`, `data_type`, `organism`, `tissue_type`, `cell_line`, `disease`, `treatment`.

### data_type
- **Ontology source**: Experimental Factor Ontology (EFO).
- **Matching**: exact label/synonym/ID → MATCHED; similarity-based → LOW_CONFIDENCE/AMBIGUOUS; fallback if allowlisted or placeholder.
- **Allowlist fallback**: optional config allowlist (`_data_type_allowlist` in `src/validator/ontology_validator.py`).
- **Locks**: terminal exact matches are locked (`ontology_terminal_exact`).
- **Non-answer placeholders**: `Unknown` with lock when detected.
- **Human curation**: triggered when unresolved failures remain after repair attempts.

### organism
- **No ontology grounding** in current pipeline.
- **Consistency**: `organism_context_conflict` if context mentions conflicting organism (`src/validator/consistency_validator.py`).
- **Non-answer placeholders**: `Unknown` with lock when detected.

### tissue_type
- **Ontology source**: Uberon.
- **Non-anatomical placeholders**: if value matches non-anatomical registry or equals disease label → fallback to `Unknown`, lock, and flag (`tissue_type_non_anatomical_placeholder`).
- **Cell type leakage**: `tissue_type_is_cell_type` from semantic validator → repair then fallback to `Unknown` (decision table).
- **Composite tissue handling (Ticket #176)**: when full-string grounding is not terminal exact, split on `&`, `/`, `,`, `;`, or word-boundary `and` and ground each fragment deterministically.
  All-components-required semantics:
  1) all fragments terminal exact → `MATCHED`, joined canonical label with `" & "` in fragment order;
  2) partial terminal exact coverage → `LOW_CONFIDENCE` + `ontology_partial_composite_tissue_type` failure/flag, no ontology-guided repair;
  3) zero terminal exact fragments → preserve existing full-string ontology behavior.
- **Locks**: terminal exact matches locked; placeholder locks override.
- **Human curation**: required for unresolved ontology failures or consistency flags.

### cell_line
- **Ontology source**: Cellosaurus.
- **Exact tie-breaking** (Ticket #97): when exact matches tie, apply
  1) raw label exact match (case-insensitive),
  2) punctuation pattern match,
  3) minimal edit distance,
  else ambiguous.
  Recorded as `tie_break_rule` in match audit.
- **Cell type leakage**: semantic `cell_line_is_cell_type` → fallback `No` (decision table).
- **Evidence missing**: `cell_line_inferred_without_evidence` triggers repair.
- **Locks**: terminal exact matches locked.

### disease
- **Ontology sources**: DOID + NCIT fallback. NCIT queried only when trigger terms match (`src/validator/grounders/disease.py`).
- **Token-equivalence** (Ticket #96 + #100): oncology synonyms normalized for scoring, including lymphoid/lymphocytic equivalence; match type `token_equiv_similarity` may produce terminal MATCHED + lock (`disease_token_equiv_similarity`).
- **Parenthetical acronym stripping (Ticket #100)**: trailing parenthetical acronyms are stripped from the **ontology query** (e.g., `X (CLL)` → `X`) while preserving `raw_value`; `query_used` reflects the cleaned query.
- **Generalizations/normalizations** (see Section 4).
- **Healthy/Unknown**: deterministic normalization when patterns match.
- **Locks**: terminal exact + token-equiv similarity + policy-driven locks.

### treatment
- **No ontology grounding**.
- **Identity leakage**: `treatment_identity_leakage` triggers deterministic fallback to `None` and flag `treatment_not_an_intervention` (Ticket #91).
  The failure must **not** fire when treatment contains intervention indicators for genetic/construct perturbations (`ko`, `knockout`, `kd`, `knockdown`, `crispr`, `sgRNA`, `shRNA`, `siRNA`, `overexpress`, `oe`, `expressing`, `transduced`, `transfected`, `clone`, `stable`, `lentivirus`, `plasmid`, `vector`, `gfp`, `egfp`) (Ticket #175).
- **Non-answer placeholders**: `None` with lock.

## 4. Disease-Specific Policies
Implemented in `src/validator/ontology_validator.py`, `src/validator/grounders/disease.py`, `src/agent/ontology_canonicalization.py`.

- **Modifier generalization (Ticket #84)**: If LOW_CONFIDENCE disease has a top alternate parent label that is a literal substring of raw disease, generalize to parent label and lock (`disease_generalized_for_ontology`).
- **Sloppy tumor normalization (Ticket #90)**: Human-only, if `tissue_type` is terminal Uberon site and raw disease matches "<site> tumor" pattern, rewrite to `"<site> cancer"`, re-ground, and lock with flag `disease_generalized_from_sloppy_tumor_label`.
- **Model identifiers (Ticket #89)**: If disease matches model patterns (e.g., CT26, MC38, B16, 4T1, LLC, "xenograft model"), set `disease = Unknown`, lock with flag `disease_model_identifier_not_ontology`, skip grounding/repair.
- **Healthy/control phrases (Ticket #92)**: Phrases like "healthy donors" normalized to terminal `Healthy`, lock with flag `disease_normalized_to_healthy`.
- **Healthy + genotype/strain (Ticket #93)**: If healthy indicators + genotype/strain tokens in non-human context, normalize to `Healthy`, lock with flag `disease_contains_genotype_context`.
- **LLM non-answer placeholders (Ticket #98)**: `Not sure`, `N/A`, `Unknown`, etc → `Unknown`, lock, and `llm_non_answer_disease` flag.
- **NCIT selection**: DOID queried first; NCIT queried only if trigger terms are present; choose higher score with tie-breaking rules (`score_preference_ncit` or `score_tie_prefer_doid`).

## 5. Tissue Type Policies
- **Anatomical-only requirement**: Tissue must be Uberon anatomy.
- **Non-anatomical placeholders** (Ticket #95): disease terms and tumor-like tokens (e.g., tumor, cancer, lymphoma, leukemia, metastasis, lesion, etc.) trigger deterministic fallback to `Unknown` with flag `tissue_type_non_anatomical_placeholder`.
- **Disease label leakage**: if tissue equals disease label (normalized), treat as non-anatomical placeholder.
- **Composite resolution (Ticket #176)**:
  1) full-string terminal exact match short-circuits composite splitting;
  2) otherwise split and evaluate each component;
  3) require terminal exact matches for all components to accept;
  4) accepted composites are canonicalized to `"label1 & label2"` form in fragment order;
  5) partial composites emit `ontology_partial_composite_tissue_type` and short-circuit repair as FLAGGED.
- **LLM non-answer placeholders**: `Unknown` with lock and `llm_non_answer_tissue_type`.

## 6. Cell Line Policies
- **Exact matches**: terminal exact matches are locked.
- **Ambiguity**: for exact-match ties, apply deterministic tie-breakers (Section 3). If unresolved → `ontology_ambiguous_cell_line` and repair.
- **Cell type leakage**: semantic `cell_line_is_cell_type` → fallback to `No`.
- **Evidence missing**: `cell_line_inferred_without_evidence` triggers repair.
- **LLM non-answer placeholders**: `Unknown` with lock and `llm_non_answer_cell_line`.

## 7. Failure Codes and Flags
Sources: `src/validator/failure_codes.py`, `spec/decision_table.yaml`, `src/agent/ontology_canonicalization.py`, `src/agent/run_single.py`, `src/agent/repair_loop.py`, `src/agent/gse_postpass.py`.

### Failure codes (decision routing)
| Code | Meaning | Trigger | Implementation |
|---|---|---|---|
| invalid_json | LLM output not valid JSON | format validator | `src/validator/format_validator.py` |
| missing_keys | Required keys missing | format validator | `src/validator/format_validator.py` |
| extra_keys | Extra keys present | format validator | `src/validator/format_validator.py` |
| word_limit_violation | Word count exceeds limit | format validator | `src/validator/format_validator.py` |
| ontology_index_unavailable | Chroma index unavailable | grounders | `src/validator/grounders/*` |
| ontology_no_match_* | No ontology match | grounders | `src/validator/ontology_validator.py` |
| ontology_ambiguous_* | Ambiguous match | grounders | `src/validator/ontology_match.py` |
| ontology_low_confidence_* | Low-confidence match | grounders | `src/validator/ontology_match.py` |
| ontology_partial_composite_tissue_type | Composite tissue has partial terminal-exact coverage | ontology validator | `src/validator/ontology_validator.py` |
| tissue_type_is_cell_type | Tissue looks like cell type | semantic validator | `src/validator/semantic_validator.py` |
| treatment_identity_leakage | Treatment looks like identity label without intervention indicators | semantic validator | `src/validator/semantic_validator.py` |
| cell_line_yes_invalid | `cell_line = yes` | semantic validator | `src/validator/semantic_validator.py` |
| cell_line_is_cell_type | Cell line looks like cell type | semantic validator | `src/validator/semantic_validator.py` |
| disease_inferred_without_evidence | Disease not supported by context | semantic validator | `src/validator/semantic_validator.py` |
| cell_line_inferred_without_evidence | Cell line not supported by context | semantic validator | `src/validator/semantic_validator.py` |
| assay_platform_conflict | Microarray vs sequencing mismatch | consistency validator | `src/validator/consistency_validator.py` |
| single_cell_evidence_missing | scRNA-seq without cues | consistency validator | `src/validator/consistency_validator.py` |
| healthy_disease_conflict | Healthy vs disease cues | consistency validator | `src/validator/consistency_validator.py` |
| organism_context_conflict | Organism mismatch | consistency validator | `src/validator/consistency_validator.py` |
| disease_unsupported | Unsupported disease → fallback | decision table | `spec/decision_table.yaml` |
| repeated_failure | Repair cycles exceeded | decision engine | `src/validator/decision_engine.py` |

### Flags (curator-facing / audit)
| Flag | Meaning | Trigger | Implementation |
|---|---|---|---|
| disease_generalized_for_ontology | Modifier→parent generalization | disease generalization | `src/agent/ontology_canonicalization.py` |
| disease_generalized_from_sloppy_tumor_label | “<site> tumor”→“<site> cancer” | sloppy tumor rule | `src/agent/ontology_canonicalization.py` |
| disease_model_identifier_not_ontology | Model ID used as disease | model identifier rule | `src/agent/ontology_canonicalization.py` |
| disease_normalized_to_healthy | Healthy/control normalized | healthy control rule | `src/agent/ontology_canonicalization.py` |
| disease_contains_genotype_context | Healthy + genotype normalized | healthy genotype rule | `src/agent/ontology_canonicalization.py` |
| tissue_type_non_anatomical_placeholder | Non-anatomical tissue | tissue placeholder rule | `src/agent/ontology_canonicalization.py` |
| ontology_partial_composite_tissue_type | Composite tissue only partially grounded | tissue composite policy | `src/validator/ontology_validator.py`, `spec/decision_table.yaml` |
| treatment_not_an_intervention | Treatment identity leakage | treatment fallback | `src/agent/ontology_canonicalization.py` |
| llm_non_answer_disease | LLM non-answer for disease | non-answer rule | `src/agent/ontology_canonicalization.py` |
| llm_non_answer_tissue_type | LLM non-answer for tissue | non-answer rule | `src/agent/ontology_canonicalization.py` |
| llm_non_answer_cell_line | LLM non-answer for cell line | non-answer rule | `src/agent/ontology_canonicalization.py` |
| format_unrepaired | Format errors left | run_single finalization | `src/agent/run_single.py` |
| max_repairs_exceeded | Repair attempts exceeded | repair loop | `src/agent/repair_loop.py` |
| repair_template_missing | Missing repair prompt | repair loop | `src/agent/repair_loop.py` |
| human_override_applied | Manual override applied | overrides | `src/agent/overrides.py` |
| gse_outlier_<field> | GSE outlier flag | GSE post-pass | `src/agent/gse_postpass.py` |

Note: consistency flags are also surfaced in audit output; `healthy_disease_conflict` is excluded from failure routing but remains in `consistency_flags`.

### Format Error Attribution (Audit-only)
- `validation.format_errors` remains the authoritative record-level set used for decision routing.
- `validation.format_error_details` provides deterministic per-field attribution for format errors without changing routing behavior.
- Current detail schema:
  - `code` (format error code),
  - `field` (triggering field),
  - `limit_used` (effective per-field word limit),
  - `observed_word_count` (whitespace-split count),
  - `stage` (`initial`, `format_repair`, or `repair_loop`).
- Detail ordering is deterministic: `code` then field order in required output schema.

## 8. Repair Templates and Fallbacks
Repair routing is defined by `spec/decision_table.yaml` and executed in `src/agent/repair_loop.py`.

| Failure | Template | LLM? | Max Attempts | Fallback | Notes |
|---|---|---|---|---|---|
| invalid_json | repair_format_v1 | Yes | 2 | none | format-level repair |
| missing_keys | repair_missing_keys_v1 | Yes | 2 | none | add required keys |
| extra_keys | repair_remove_extra_keys_v1 | Yes | 2 | none | remove extra keys |
| word_limit_violation | repair_shorten_values_v1 | Yes | 2 | none | shorten values |
| ontology_* (no/amb/low) | repair_ontology_guided_v1 | Yes | 2 | none | per-field ontology repair |
| ontology_partial_composite_tissue_type | none | No | 0 | none | deterministic escalate; composite tissue all-components-required policy |
| tissue_type_is_cell_type | repair_tissue_anatomy_v1 | Yes | 1 | Unknown | anatomy correction |
| assay_platform_conflict | repair_data_type_from_context_v1 | Yes | 2 | Unknown | data_type repair |
| single_cell_evidence_missing | repair_data_type_from_context_v1 | Yes | 2 | Unknown | data_type repair |
| healthy_disease_conflict | repair_disease_from_context_v1 | Yes | 2 | Unknown | disease repair |
| disease_inferred_without_evidence | repair_disease_evidence_v1 | Yes | 1 | none | evidence-based disease repair |
| cell_line_inferred_without_evidence | repair_cell_line_evidence_v1 | Yes | 1 | none | evidence-based cell line repair |
| cell_line_is_cell_type | none | No | 0 | No | deterministic fallback |
| disease_unsupported | none | No | 0 | Healthy | deterministic fallback |
| treatment_identity_leakage | none | No | 0 | none | deterministic fallback to None via policy; suppressed when intervention indicators are present |
| organism_context_conflict | none | No | 0 | none | escalated |
| repeated_failure | none | No | 0 | none | escalated |

Terminal fallback values are recorded and prevent further repairs for that field in the same run (`src/agent/repair_loop.py`).

## 9. Final Decision Logic
- **ACCEPT**: no unresolved failures after repair loop, or failures mapped to ACCEPT in the decision table.
- **FLAGGED**: any unresolved failure after repair loop, format errors left unrepaired, or explicit policy flags that force non-accept (e.g., `tissue_type_non_anatomical_placeholder`, `disease_model_identifier_not_ontology`).
- **REJECT**: reserved for unrecoverable errors (not currently emitted by decision table; escalation yields FLAGGED).

Locked fields always take precedence in final output assembly (`_apply_locked_field_values` in `src/agent/run_single.py`).

## 10. Traceability Notes
- **Tickets v0.9+**: behavior introduced by tickets #84–#99 is explicitly labeled in flags and matched_via values.
- **Legacy behavior**: policies without ticket identifiers in code are **pre-v0.9 legacy behavior** (e.g., base ontology matching thresholds, format validation rules, standard repair templates).
