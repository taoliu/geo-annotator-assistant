Ticket #4: AGENT-WS-004 Implement semantic field validator (+ unit tests)

You are working in repo `geo-gsm-annotator-agent` (src-layout under `src/`).

Ticket: AGENT-WS-004 — Implement semantic field validator (+ unit tests)

Goal:
Implement deterministic, pattern-based semantic validation on parsed LLM output.
This validator does NOT call ontologies or Chroma. It only flags obvious rule violations.

Files:
- Review/update `src/validator/semantic_validator.py` (exists in skeleton).
- Add unit tests `tests/test_semantic_validator.py`.

Public API:
- `semantic_validate(parsed_output: dict[str,str], context_text: str) -> dict[str, list[str]]`

Failure codes (exact strings):
- `tissue_is_cell_type`
- `treatment_identity_leakage`
- `cell_line_yes_invalid`
- `disease_inferred_without_evidence`

Rules:

1) tissue_type:
- If tissue_type is missing or equals "Unknown": no error.
- Otherwise flag `tissue_is_cell_type` if tissue_type likely describes a cell type.
  Implement conservative heuristics:
  - contains whole word "cell" or "cells" (case-insensitive) OR
  - ends with common cell-type suffixes like "cells", "cell", "lymphocyte", "neuron", "macrophage"
  Keep this list small and editable.

2) treatment:
- If treatment missing or equals "None": no error.
- Otherwise flag `treatment_identity_leakage` if treatment contains any identity concepts.
  Conservative patterns:
  - whole word "cell"/"cells"
  - genotype-like tokens: "KO", "knockout", "transgenic", "+/+", "+/-", "-/-", "Cre"
  - tissue words: "liver", "brain", "blood", "intestine" (small list)
  Keep the list small and editable.

3) cell_line:
- If equals "Yes" (case-insensitive): flag `cell_line_yes_invalid`.
- "No" is fine; any other string is fine here (ontology will validate later).

4) disease:
- If disease missing or equals "Healthy": no error.
- Otherwise flag `disease_inferred_without_evidence` ONLY when context_text has no disease cues.
  Use a small cue list in lowercase:
  ["disease", "tumor", "cancer", "carcinoma", "leukemia", "lymphoma", "infection", "patient", "diagnos"]
  If none appear in context_text.lower(), flag.

Output:
- Dict keyed by field name with list of failure codes.
- Deterministic order: for each field, codes should be sorted in stable order (only one per rule here).
- If no issues, return empty dict.

Unit tests (pytest):
Create `tests/test_semantic_validator.py` with at least:
- tissue_type "intestinal epithelial cells" -> tissue_is_cell_type
- tissue_type "Small intestine" -> no error
- treatment "Lgr5-GFP cells, no treatment" -> treatment_identity_leakage
- treatment "None" -> no error
- cell_line "Yes" -> cell_line_yes_invalid
- disease "Breast cancer" with context lacking cues -> disease_inferred_without_evidence
- disease "Breast cancer" with context containing "cancer" -> no error

Constraints:
- No ontology calls
- No external deps besides stdlib + pytest
- Keep code simple and readable
- Do not change other modules unless necessary

After implementation:
- run `uv run python -m pytest -q` and ensure all tests pass.

Deliverables:
- updated `src/validator/semantic_validator.py`
- new `tests/test_semantic_validator.py`
