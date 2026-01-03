Ticket #10: AGENT-WS-010 Implement JSONL output writer with atomic writes (+ unit tests)

This adds the first real artifact output and is still low-risk.

You are working in repo `geo-gsm-annotator-agent` (src-layout under `src/`).

Ticket: AGENT-WS-010 — Implement JSONL output writer with atomic writes (+ unit tests)

Goal:
Implement a writer that outputs:
- annotations.jsonl (primary outputs)
- audit.jsonl (audit records)
- flagged.jsonl (subset needing human review)
Use atomic write strategy for each file: write to temp file, then rename.

Files to implement/update:
- `src/agent/writer.py` (currently placeholder)
- Add tests: `tests/test_writer.py`

Writer requirements:
1) Provide functions:
   - `write_jsonl(path: str, records: list[dict]) -> None`
   - `write_run_outputs(output_dir: str, annotations: list[dict], audits: list[dict], flagged: list[dict]) -> dict`
     returns dict of written file paths

2) JSONL rules:
- One JSON object per line
- UTF-8
- Ensure records are JSON-serializable (raise ValueError with helpful message if not)
- Preserve key order as given by dict (no need to sort)

3) Atomic write:
- Write to `{path}.tmp` then `os.replace(tmp, path)`
- Ensure output_dir exists (create)

4) Default filenames in write_run_outputs:
- annotations.jsonl
- audit.jsonl
- flagged.jsonl

Unit tests:
Create `tests/test_writer.py`:
- Use pytest tmp_path fixture
- Write a small list of dicts and verify:
  - files exist
  - line count matches record count
  - each line is valid JSON and equals original dict content
- Test atomic behavior indirectly:
  - call write_jsonl twice on same path with different content, ensure final file matches second content
- Test serialization failure:
  - record containing unserializable object (e.g., set()) raises ValueError

Constraints:
- Only stdlib + pytest
- No changes to CLI yet

After implementation:
- run `uv run python -m pytest -q`

Deliverables:
- `src/agent/writer.py`
- `tests/test_writer.py`

