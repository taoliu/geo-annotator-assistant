Ticket #1: AGENT-WS-001 Implement CLI dry-run with config and prompt loading (walking skeleton)

You are working in the repo `geo-gsm-annotator-agent` (Python, src-layout under `src/`).
Goal: implement the first “walking skeleton” step so that the CLI can run in dry-run mode and load config + prompt templates.

Scope:
- Implement minimal config loader (YAML) and prompt template loader.
- Update CLI to support: --gsm, --gsm-file, --output-dir, --config, --dry-run
- For now, DO NOT implement the full pipeline, LLM, parser, or validators. Just prove wiring works.

Required behavior:
1) `python -m agent.cli --gsm GSM000000 --config config/example_config.yaml --dry-run`
   - loads YAML config
   - loads prompt templates from `prompts/` directory
   - prints a short summary to stdout and exits 0
   - summary must include:
     - gsm(s) count
     - config versions.prompt_version and versions.validator_version (if present)
     - rag.persist_path
     - rag.collections keys present
     - list of loaded prompt template filenames

2) `python -m agent.cli --gsm-file <file> --config <cfg> --dry-run`
   - reads GSM ids (one per line, ignores blank lines and lines starting with #)
   - prints count and exits 0

Implementation details:
- Create `src/agent/config.py`:
  - function `load_config(path: str) -> dict`
  - validate file exists; raise ValueError with helpful message if missing/invalid
- Create `src/agent/prompts.py`:
  - function `load_prompts(prompt_dir: str) -> dict[str, str]`
  - load all *.txt files; return mapping filename->content
  - raise ValueError if directory missing or no txt files
- Update `src/agent/cli.py`:
  - implement argparse CLI:
    - mutually exclusive --gsm and --gsm-file
    - --output-dir default "outputs"
    - --config required
    - --dry-run boolean
  - in dry-run, do not write files
  - compute prompt_dir relative to repo root; simplest: default "prompts" directory in current working directory; allow override from config if you want, but not required
  - print summary lines with clear labels (no JSON needed)
  - exit with code 0 on success, 1 on argument error, 2 on runtime error (catch exceptions in main)

Constraints:
- Keep dependencies minimal: only use standard library + pyyaml (already in requirements).
- Do not change pyproject.toml or requirements.
- Keep code style simple and readable.
- Add small docstrings.

After implementation, ensure:
- `python -m agent.cli --help` works
- Dry-run commands above run without exceptions.

Deliverables:
- src/agent/config.py
- src/agent/prompts.py
- updated src/agent/cli.py

Status: In Progress

Owner: Codex

Blocks: everything else
