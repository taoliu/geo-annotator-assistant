Ticket #6: AGENT-WS-006 Implement thresholds + ontology validator entrypoint (+ unit tests)

You are working in repo `geo-gsm-annotator-agent` (src-layout under `src/`).

Ticket: AGENT-WS-006 — Implement thresholds + ontology validator entrypoint (+ unit tests)

Goal:
Implement the per-field threshold logic and an ontology grounding validator entrypoint that:
- calls per-field grounders
- applies thresholds to decide pass/fail
- returns structured matches + failure codes

IMPORTANT:
Grounder modules in `src/validator/grounders/` are currently placeholders. For this ticket:
- you must implement `validator/ontology_validator.py` so that it calls the grounders IF they exist,
  but also works even if a grounder is still a placeholder.
- You should implement a minimal safe fallback: if a grounder raises NotImplementedError or returns a placeholder string, treat as no match.

Files to implement/update:
1) `src/validator/thresholds.py` (currently placeholder)
2) `src/validator/ontology_validator.py` (currently placeholder)

Use existing model:
- `OntologyMatch` in `src/validator/ontology_match.py`

Failure codes for ontology validator:
- `ontology_no_match`
- `ontology_low_score`

Public APIs:

A) thresholds.py
- `get_threshold(field: str, thresholds_cfg: dict | None = None) -> float`
- `is_match_acceptable(field: str, match: OntologyMatch, thresholds_cfg: dict | None = None) -> bool`

Rules:
- If match.match_type == "fallback": always acceptable
- If match.match_type == "none": not acceptable
- If match.score is None: not acceptable unless fallback
- Otherwise acceptable if match.score >= threshold(field)
- Provide defaults in code:
  data_type: 0.75
  tissue_type: 0.75
  cell_line: 0.80
  disease: 0.75
- Allow override via thresholds_cfg dict (same keys as fields)

B) ontology_validator.py
Implement:
- `ground_all_fields(llm_output: dict[str,str], context_text: str, rag_config: dict) -> tuple[dict[str, OntologyMatch], dict[str, str]]`
Where:
- first return is matches_by_field for the 4 ontology-driven fields:
  data_type, tissue_type, cell_line, disease
- second return is failures_by_field mapping field -> failure_code (only for failed fields)

Inputs:
- llm_output: output dict from format validator (already stripped strings)
- context_text: parsed GSM/GSE text
- rag_config: dict from YAML config. For this ticket, you only need:
  rag_config["persist_path"]
  rag_config["collections"] mapping ontology -> collection name
  rag_config.get("k", 10)
  rag_config.get("thresholds") or separate thresholds_cfg passed later (you can accept thresholds_cfg from rag_config if present)

Grounder calling:
- Call these functions (import them):
  - `ground_data_type` from `validator.grounders.data_type`
  - `ground_tissue_type` from `validator.grounders.tissue_type`
  - `ground_cell_line` from `validator.grounders.cell_line`
  - `ground_disease` from `validator.grounders.disease`
- Each should return OntologyMatch.

But since grounders are placeholders now:
- Wrap each call in try/except.
- If the module is placeholder and does not define the function, or it raises NotImplementedError, produce an OntologyMatch with:
  match_type="none", score=None, matched_term_id=None, matched_label=None, ontology set appropriately.

Acceptance logic:
- Use `is_match_acceptable()` from thresholds.py
- If not acceptable:
  - if match.match_type == "none" OR match.score is None -> `ontology_no_match`
  - else -> `ontology_low_score`

Special handling of fallbacks:
- If raw_value is fallback value:
  tissue_type == "Unknown" -> acceptable fallback
  cell_line == "No" -> acceptable fallback
  disease == "Healthy" -> acceptable fallback
- The grounder may return fallback match_type, but if not implemented, you can detect these raw values and create fallback OntologyMatch yourself in ontology_validator.py.

Unit tests:
Create `tests/test_thresholds_and_ontology_validator.py` with pytest tests.
Do NOT depend on ChromaDB.
Strategy:
- Monkeypatch or create dummy grounder functions by temporarily injecting them (e.g., import module and set attribute) OR
  design ontology_validator to accept optional callables for grounders (preferred, if you can do it cleanly without breaking API).

Test cases:
1) thresholds: match score 0.8 for cell_line -> acceptable
2) thresholds: match score 0.7 for cell_line -> not acceptable
3) fallback: tissue_type Unknown -> acceptable and no failures
4) placeholder grounder: raises NotImplementedError -> ontology_no_match failure
5) low score: returns score 0.5 -> ontology_low_score failure

Constraints:
- Keep it deterministic.
- No external deps besides stdlib + pytest.
- Do not implement full RAG retrieval here.

After implementation:
- run `uv run python -m pytest -q` and ensure tests pass.

Deliverables:
- `src/validator/thresholds.py`
- `src/validator/ontology_validator.py`
- `tests/test_thresholds_and_ontology_validator.py`
