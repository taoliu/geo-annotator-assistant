# Ticket #57: CLI-STD-002 — Polish `standardize-terms` CLI ergonomics, defaults, and console script wiring

## Background

Ticket #56 introduced a new deterministic backend CLI subcommand:

```
geo-gsm-annotate standardize-terms
```

The core functionality is complete and correct. However, the current command-line interface needs **ergonomic polish** to support real curator workflows and to align with standard Unix CLI expectations.

This ticket focuses exclusively on **CLI usability, defaults, and packaging clarity**, without changing any grounding, canonicalization, or backend semantics.

---

## Scope (STRICT)

### In scope

1. **Short-form CLI flags**

   Add conventional short aliases while preserving all existing long flags:

   | Long flag  | Short flag |
   | ---------- | ---------- |
   | `--input`  | `-i`       |
   | `--output` | `-o`       |
   | `--audit`  | `-a`       |
   | `--config` | `-c`       |
   | `--fields` | `-f`       |

   Short flags must be purely aliases and must not change behavior.

---

2. **Sane and deterministic default values**

   Implement the following defaults:

   * If `--output` is not provided:

     ```
     <input>.standardized.jsonl
     ```

   * If `--audit` is not provided:

     ```
     <output>.audit.jsonl
     ```

   * If `--fields` is not provided:

     * Default to **all ontology-backed fields supported by the command**
       (as implemented in Ticket #56).

   * Canonicalization flag behavior:

     * Default behavior must be **“respect config”**.
     * CLI flags may override config explicitly, but absence of flags must not alter config-driven behavior.

   Defaults must be computed deterministically and documented in `--help`.

---

3. **Help text and discoverability**

   * `--help` output must:

     * clearly list all defaults
     * describe each flag in one concise sentence
     * include at least one example invocation

   Example section (illustrative):

   ```
   Examples:
     geo-gsm-annotate standardize-terms -i curated.jsonl
     geo-gsm-annotate standardize-terms -i curated.jsonl -o out.jsonl -f disease,cell_line
   ```

---

4. **CLI structure and module hygiene**

   * Keep **one backend console script**:

     ```
     geo-gsm-annotate = agent.cli:main
     ```

   * `standardize-terms` must remain a **subcommand** of `geo-gsm-annotate`.

   * Refactor implementation if needed so that:

     * argument parsing and execution logic for `standardize-terms`
       live in a dedicated module (for example `agent.standardize_cli`)
     * `agent.cli` remains a thin dispatcher

   No new console scripts may be added.

---

5. **`pyproject.toml` review (non-semantic)**

   * Confirm console script definitions are correct and minimal.
   * Update only if required for clarity or correctness.
   * No behavior change allowed.

---

## Explicitly Out of Scope

* CSV support
* Any change to:

  * ontology grounding
  * canonicalization logic
  * match scoring
  * thresholds
  * config schema
* UI changes
* Persistence or learning

---

## Acceptance Criteria

1. Users can run:

   ```
   geo-gsm-annotate standardize-terms -i curated.jsonl
   ```

   and obtain deterministic output and audit files using defaults.

2. Short flags behave identically to long flags.

3. `--help` output clearly documents:

   * defaults
   * examples
   * subcommand purpose

4. Existing Ticket #56 behavior remains unchanged when explicit arguments are supplied.

5. All tests pass:

   ```
   uv run pytest -q
   ```

---

## Tests Required

Add or update unit tests under `tests/`:

1. **Argument default resolution**

   * Input only → derived output and audit paths are correct.

2. **Short flag parsing**

   * `-o`, `-a`, `-f` correctly map to long options.

3. **Help text sanity**

   * `--help` output contains documented defaults and examples.

4. **Console script exposure**

   * `geo-gsm-annotate --help` lists `standardize-terms` as a subcommand.

Tests must not rely on real ontology data.

---

## Ticket file requirement (MANDATORY)

Create `docs/tickets/ticket-57.md` and paste this ticket **verbatim**.

---
