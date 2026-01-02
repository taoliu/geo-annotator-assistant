Ticket #11: AGENT-WS-011 — Wire CLI to single/batch pipeline and write outputs (+ unit tests)

This is the final step to complete the walking skeleton as a usable command.

You are working in repo `geo-gsm-annotator-agent` (src-layout under `src/`).

Ticket: AGENT-WS-011 — Wire CLI to single/batch pipeline and write outputs (+ unit tests)

Goal:
Update the CLI so it can:
- run single GSM or a list of GSMs (batch)
- call run_single_gsm for each GSM
- write outputs using writer functions unless --dry-run
- print a short summary
This should work end-to-end with stub parser/LLM.

Files to implement/update:
- `src/agent/cli.py`
- `src/agent/run_batch.py` (currently placeholder; implement simple batch loop)
- Add tests: `tests/test_cli_and_batch.py`

Requirements:

A) Implement run_batch (agent/run_batch.py)
Public API:
- `run_batch(gsms: list[str], cfg: dict) -> tuple[list[dict], list[dict], list[dict], dict]`
Returns:
- annotations: list of primary outputs
- audits: list of audit records
- flagged: list of primary outputs for flagged samples (or include audit too if you prefer, but be consistent)
- summary: dict with counts:
  - n_total, n_accepted, n_flagged

Behavior:
- For each GSM, call `run_single_gsm(gsm, cfg)`
- If a GSM crashes, catch exception and count as flagged:
  - create minimal annotation record with gsm_accession and placeholders
  - create minimal audit record with error message and final_decision="FLAGGED"
- Deterministic ordering: preserve GSM input order.

B) Update CLI (agent/cli.py)
- Parse args:
  - --gsm (single)
  - --gsm-file (list)
  - --output-dir
  - --config (required)
  - --dry-run
- Load cfg via `agent.config.load_config`
- For walking skeleton, leave cfg parser/llm modes as configured (example_config uses stub by default)
- If single: call run_single_gsm; wrap into lists
- If batch: call run_batch
- If not dry-run:
  - call `agent.writer.write_run_outputs(output_dir, annotations, audits, flagged)`
- Print summary:
  - total, accepted, flagged
  - output paths (if written)
  - if dry-run, say "Dry-run: no files written"
- Exit codes:
  - 0 success
  - 1 argument error
  - 2 runtime error

C) Unit tests (pytest)
Create `tests/test_cli_and_batch.py` with tests focusing on run_batch and CLI core behavior.
Avoid invoking subprocess. Call functions directly.

Test cases:
1) run_batch with 2 GSMs using stub config:
   - n_total=2
   - n_flagged=0
   - annotations length=2, audits length=2
2) run_batch where one GSM is forced to fail:
   - simplest: monkeypatch agent.run_single.run_single_gsm to raise for a specific GSM
   - ensure n_flagged=1 and still returns 2 records
3) writer integration:
   - call write_run_outputs with tmp_path and outputs from run_batch, verify files exist and line counts match.

Constraints:
- Only stdlib + pytest
- No external calls
- Keep code clean

After implementation:
- run `uv run python -m pytest -q`

Manual smoke test you should be able to run after:
- `uv run python -m agent.cli --gsm GSM000000 --config config/example_config.yaml --output-dir /tmp/out`
- It should write three jsonl files.

Deliverables:
- updated `src/agent/cli.py`
- `src/agent/run_batch.py`
- `tests/test_cli_and_batch.py`
