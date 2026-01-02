Ticket #5: AGENT-WS-005 Implement cross-field consistency validator (+ unit tests)

You are working in repo `geo-gsm-annotator-agent` (src-layout under `src/`).

Ticket: AGENT-WS-005 — Implement cross-field consistency validator (+ unit tests)

Goal:
Implement deterministic, keyword-based cross-field consistency checks.
No ontology calls. No Chroma calls. No repair logic.

Files:
- Review/update `src/validator/consistency_validator.py` (exists in skeleton).
- Add unit tests `tests/test_consistency_validator.py`.

Public API:
- `consistency_validate(parsed_output: dict[str,str], context_text: str) -> list[str]`

Flags (exact strings):
- `assay_platform_conflict`
- `single_cell_evidence_missing`
- `healthy_disease_conflict`
- `organism_context_conflict`

Rules:

1) single_cell_evidence_missing
- If data_type (case-insensitive) is one of:
  {"scrna-seq", "snrna-seq", "scatac-seq", "snatac-seq"}
  then require at least one single-cell/nucleus keyword in context_text.lower().
  Use small list: ["single cell", "single-cell", "single nucleus", "single-nucleus", "10x", "chromium", "drop-seq", "smart-seq"]
  If none, add flag.

2) assay_platform_conflict
- If data_type == "Microarray" (case-insensitive equals "microarray"):
  If context contains sequencing cues like:
  ["rna-seq", "atac-seq", "chip-seq", "nextseq", "novaseq", "hiseq", "miseq", "sequencing"]
  then add assay_platform_conflict.

3) healthy_disease_conflict
- If disease == "Healthy":
  If context contains strong disease cues:
  ["tumor", "cancer", "carcinoma", "leukemia", "lymphoma", "disease:"]
  then add healthy_disease_conflict.

4) organism_context_conflict
- If organism == "Mus musculus" but context contains "Homo sapiens" -> conflict.
- If organism == "Homo sapiens" but context contains "Mus musculus" -> conflict.
Case-insensitive.

Output:
- Return a sorted unique list of flags.
- Empty list if none.

Unit tests (pytest):
Create `tests/test_consistency_validator.py` with at least:
- scRNA-seq with no single-cell cues -> single_cell_evidence_missing
- scRNA-seq with "single-cell" in context -> no flag
- microarray with "RNA-seq" in context -> assay_platform_conflict
- Healthy with "cancer" in context -> healthy_disease_conflict
- organism Mus musculus with context Homo sapiens -> organism_context_conflict
- a clean case produces [].

Constraints:
- Only stdlib + pytest
- Deterministic behavior
- Do not change other modules unless necessary

After implementation:
- run `uv run python -m pytest -q` and ensure all tests pass.

Deliverables:
- updated `src/validator/consistency_validator.py`
- new `tests/test_consistency_validator.py`
