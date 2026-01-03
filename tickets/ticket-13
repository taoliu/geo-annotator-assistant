Ticket #13: AGENT-WS-013 — Add GSE-mode pipeline (read parsed JSONL contexts, assemble prompts, run batch)



You are working in repo `geo-gsm-annotator-agent` (src-layout under `src/`).

Ticket: AGENT-WS-013 — Add GSE-mode pipeline (read parsed JSONL contexts, assemble prompts, run batch)

Context:
We now have an ingest script that outputs a JSONL file where each row is:
{
  "context_text": "...",
  "gsm_accession": "GSM3071332",
  "gse_accession": "GSE112494"
}
The instruction prompt is stored in `prompts/label_v1.txt` and should be prepended by the agent.

Goal:
Implement a new pipeline path that can take:
- a GSE accession (download + construct JSONL) OR
- a prebuilt JSONL file (preferred for debugging)
and run the annotation agent for each GSM record in the JSONL.

In this ticket, the LLM can remain stubbed (cfg["llm"]["mode"]="stub") but the pipeline must:
- read JSONL records (context_text, gsm_accession, gse_accession)
- assemble final prompt: label prompt template + context_text
- run existing validation/decision/audit/writer flow per GSM
- write outputs grouped for the GSE (in output dir)

Files to implement/update:

A) New module: `src/ingest/read_context_jsonl.py`
- function `iter_gsm_contexts(jsonl_path: str) -> Iterator[dict]`
  - yields dicts with keys: context_text, gsm_accession, gse_accession
  - ignores blank lines
  - validates required keys and types (strings)
  - raises ValueError with line number on malformed rows

B) Update `src/agent/run_single.py`
Add a new entrypoint (do not break existing run_single_gsm):
- `run_single_from_context_record(record: dict, cfg: dict) -> tuple[dict, dict, bool]`
Behavior:
- record has gsm_accession/gse_accession/context_text
- Create PipelineState from these values
- Build final_prompt = label prompt template + "\n\n" + record["context_text"]
  - Load templates using existing prompt loader (agent.prompts.load_prompts or similar)
  - Respect cfg["versions"]["prompt_version"] to select label prompt filename:
    - if prompt_version == "v1" use "label_v1.txt"
    - (future versions can be added later)
- LLM call:
  - if cfg["llm"]["mode"] == "stub": return a valid JSON output (same as before), but set gse/gsm from record.
  - else: leave placeholder call path (no real integration required in this ticket).
- Validators should use context_text from record (not full prompt).
- Proceed with the same flow as run_single_gsm:
  format -> semantic -> consistency -> ontology -> repairs -> audit.
- Ensure primary_output has exactly 8 keys as before.
Return same tuple.

Keep existing `run_single_gsm(gsm_accession, cfg)` working. It may remain as stub parser path for now.

C) New module: `src/agent/run_gse.py`
Implement:
- `run_gse_from_jsonl(jsonl_path: str, cfg: dict) -> tuple[list[dict], list[dict], list[dict], dict]`
Behavior:
- iterate records via ingest.read_context_jsonl.iter_gsm_contexts
- for each record call run_single_from_context_record
- collect annotations/audits/flagged + summary counts (same shape as run_batch)
- preserve order from JSONL
- catch exceptions per GSM and create flagged audit/annotation record (like run_batch)

Optional (nice): `run_gse(gse_accession: str, cfg: dict) -> ...`
- use existing ingest modules if present:
  - download soft: `python -m ingest.gse_soft_fetcher ...` OR import a function if available
  - construct prompt jsonl: `python -m ingest.construct_prompt ...`
But this ticket can focus on JSONL input only if simpler.
If you implement run_gse(gse_accession), put outputs under output_dir/<GSE>/ by default.

D) Update CLI: `src/agent/cli.py`
Add new mutually exclusive option group:
- --gsm
- --gsm-file
- --jsonl (path to context JSONL as described)
- --gse (GSE accession)
Rules:
- Exactly one input source required.
Behavior:
- If --jsonl: call run_gse_from_jsonl
- If --gse: if you implement run_gse, call it; otherwise raise a clear error telling user to use --jsonl for now.
Writing:
- use writer.write_run_outputs as before
- If input is gse/jsonl and the records all share one gse_accession:
  - create output directory output_dir/<GSE>/ and write there
  - else write to output_dir directly

E) Unit tests
Add `tests/test_gse_jsonl_path.py`:
- Create a temp jsonl file with 2 records (two GSMs, same GSE)
- Load cfg (example_config) and force llm.mode=stub
- Call run_gse_from_jsonl and assert:
  - counts are correct
  - annotations have correct gsm_accession and gse_accession
  - flagged=0
- Also test malformed row (missing context_text) raises ValueError with line info

Also add a small CLI wiring test (optional if easy) by calling the CLI main function with args list, or by testing the decision branch logic without subprocess.

Constraints:
- No external network calls
- Keep code deterministic
- Keep code simple; no heavy refactors
- Preserve existing tests; all tests must pass

After implementation:
- run `uv run python -m pytest -q` and ensure passing

Deliverables:
- src/ingest/read_context_jsonl.py
- updated src/agent/run_single.py (new run_single_from_context_record)
- src/agent/run_gse.py
- updated src/agent/cli.py
- tests/test_gse_jsonl_path.py
