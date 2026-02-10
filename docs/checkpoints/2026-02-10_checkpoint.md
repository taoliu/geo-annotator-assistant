# Checkpoint — 2026-02-10

## System Status

**Stable, production-ready**

This checkpoint captures the authoritative system state after completion of
**Milestone v1.2 (CLI Ergonomics & Agent Invocation Refinement)**.

Backend semantics remain frozen as of v0.9. Curator UI v1.1 is complete and in active use.
All changes in v1.2 are limited to CLI ergonomics, ingest robustness, performance plumbing,
and post-curation summarization.

---

## Architectural Invariants

Unchanged.

- Whitepaper (`docs/whitepaper.md`) remains fully authoritative.
- Output schema remains exactly 8 GSM-level fields.
- Pipeline order, validation, repair, ontology grounding, and decision routing are unchanged.
- GSMs remain independent decision units.
- Human overrides remain explicit, auditable, and post-processing only.

---

## CLI Surface (Authoritative)

### `geo-gsm-annotate`

Primary agent execution command.

Key characteristics:
- Supports single-GSE and multi-GSE batch runs.
- Batch behavior is always explicit (no implicit inference).
- Expensive runtime resources are reused per invocation:
  - LLMs (for local transformer backends)
  - Chroma client and ontology collections
- Provides step-level observability via `--verbose`.
- Uses local-first GEO SOFT ingest with configurable remote fallback.
- Self-heals incomplete or corrupted local SOFT files via re-download and retry.

Responsibilities:
- Generate proposed annotations.
- Perform validation, repair, grounding, and decision routing.
- Emit authoritative output and audit artifacts.

Explicitly does **not**:
- Apply curator overrides.
- Perform summarization or reporting.

---

### `geo-gsm-summarize`

Standalone, read-only post-curation summarization command.

Key characteristics:
- Reads existing output directories only.
- Applies curator overrides.
- Does not invoke LLMs or backend processing.
- Exports:
  - GSM-level CSV (8 canonical fields).
  - GSE-level CSV (7 fields; GSM accession removed).
- Reuses the same summarization logic as the curator UI.

This command is the **only CLI entry point** that applies curator overrides.

---

## Ingest Behavior (GEO SOFT)

Current ingest behavior is:

1. Resolve SOFT file from local repository if configured.
2. If missing or unparsable:
   - Download fresh copy from remote (FTP or HTTPS, configurable).
   - Store into the repository directory.
   - Retry parsing exactly once.
3. If parsing still fails:
   - Skip or error according to configured policy.

This behavior ensures:
- Robust batch execution.
- Self-healing of incomplete local repositories.
- Deterministic and auditable ingest.

---

## Performance Characteristics

After v1.2:

- LLM model loading occurs once per CLI invocation (local backends only).
- Chroma vector database client and collections are initialized once per process.
- Ontology grounding performance is stable and predictable across large batches.
- First-use penalties are amortized across GSMs and GSEs.

When combined with node-local storage (e.g. TMPDIR on clusters), the system performs
efficiently on shared HPC environments.

---

## Output Artifacts (Unchanged)

Per GSE output directory includes:

- `annotations.jsonl` — final GSM annotations (8 fields)
- `audit.jsonl` — decision trace and diagnostics
- `evidence.jsonl` — evidence records
- `suggestions.jsonl` — optional cross-GSM advisory hints

These artifacts remain the sole authoritative backend outputs.

---

## Curator Workflow (Authoritative)

The intended end-to-end workflow is now:

1. Prepare a YAML configuration.
2. Run `geo-gsm-annotate` on GSE(s).
3. Review and curate results in the web UI.
4. Export final CSVs using `geo-gsm-summarize`.

This separation is enforced by CLI design and documentation.

---

## Known Deferred Items

The following were identified but intentionally deferred beyond v1.2:

- README.md refresh (to be handled by a code-aware agent).
- Removal of `--overrides` from `geo-gsm-annotate`.
- Optional ontology warmup hooks.
- Environment-variable expansion in config paths.

None of these affect correctness or stability.

---

## Readiness Assessment

- ✅ Backend: stable and policy-governed
- ✅ CLI: batch-safe, observable, and cluster-friendly
- ✅ UI: stable and curator-trustworthy
- ✅ Reporting: explicit, reproducible, and override-aware

The system is ready for transition to the next milestone.
