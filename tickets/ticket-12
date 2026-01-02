Ticket #12: AGENT-WS-012 — Externalize heuristic keyword lists into spec/heuristics.yaml (no behavior change)

Goal: Move all hardcoded keyword lists and small heuristic sets used by:

* validator/semantic_validator.py
* validator/consistency_validator.py

into one YAML file, loaded via a small helper module. Validators should behave the same as before.

You are working in repo `geo-gsm-annotator-agent`.

Ticket: AGENT-WS-012 — Externalize heuristic keyword lists into spec/heuristics.yaml (no behavior change)

Goal:
Move hardcoded keyword lists/regex patterns used in:
- `src/validator/semantic_validator.py`
- `src/validator/consistency_validator.py`
into a YAML file `spec/heuristics.yaml`, loaded by a new helper `src/validator/heuristics.py`.
No behavior change: all existing tests must still pass.

Tasks:

A) Create `spec/heuristics.yaml`
Include sections:

semantic:
  tissue_cell_keywords: ["cell", "cells"]
  tissue_cell_suffixes: ["cells", "cell", "lymphocyte", "neuron", "macrophage"]
  treatment_identity_keywords: ["cell", "cells"]
  treatment_genotype_keywords: ["ko", "knockout", "transgenic", "+/+", "+/-", "-/-", "cre"]
  treatment_tissue_keywords: ["liver", "brain", "blood", "intestine"]

  disease_cues: ["disease", "tumor", "cancer", "carcinoma", "leukemia", "lymphoma", "infection", "patient", "diagnos"]

consistency:
  single_cell_data_types: ["scRNA-seq", "snRNA-seq", "scATAC-seq", "snATAC-seq"]
  single_cell_keywords: ["single cell", "single-cell", "single nucleus", "single-nucleus", "10x", "chromium", "drop-seq", "smart-seq"]

  microarray_data_type: "Microarray"
  sequencing_keywords: ["rna-seq", "atac-seq", "chip-seq", "nextseq", "novaseq", "hiseq", "miseq", "sequencing"]

  healthy_value: "Healthy"
  disease_keywords: ["tumor", "cancer", "carcinoma", "leukemia", "lymphoma", "disease:"]

  organism_conflicts:
    - ["Mus musculus", "Homo sapiens"]

(Use exactly the lists currently embedded in validators if they differ; the goal is no behavior change.)

B) Create `src/validator/heuristics.py`
Implement:
- `load_heuristics(path: str = "spec/heuristics.yaml") -> dict`
  - loads YAML
  - raises ValueError if missing/invalid
- `get_heuristics(path: str = "spec/heuristics.yaml") -> dict`
  - cached load (module-level cache ok)
- Provide a `DEFAULT_HEURISTICS` dict fallback inside the module for robustness.
  - If file missing, return DEFAULT_HEURISTICS (do not crash), but document this.
For tests, file will exist, so it should load from YAML.

C) Update `semantic_validator.py` to use heuristics from `get_heuristics()`
- Replace hardcoded lists with loaded values.
- Keep regex compilation but build patterns from YAML lists.
- Preserve failure codes and output format.

D) Update `consistency_validator.py` to use heuristics from `get_heuristics()`
- Replace hardcoded keyword lists with loaded values.
- Preserve flags and output format.

E) Tests
- Do not change existing tests unless absolutely necessary.
- Add one new test `tests/test_heuristics_loading.py`:
  - calls `get_heuristics()` and asserts required sections/keys exist.
  - ensures lists are non-empty.

Acceptance criteria:
- `uv run python -m pytest -q` passes all existing tests.
- Behavior is unchanged.
- Heuristic lists are reviewable in one YAML file.

Deliverables:
- spec/heuristics.yaml
- src/validator/heuristics.py
- updated semantic_validator.py
- updated consistency_validator.py
- tests/test_heuristics_loading.py
