# Ticket #79: Improve context_fingerprint normalization for replicate GSMs (normalize replicate indicators and ignore Sample Filename)

## Problem

Per-GSE LLM caching uses `context_fingerprint`, but replicate GSMs often differ only by:

* numeric replicate indicators in `Sample Title` (e.g., “replicate 1” vs “replicate 2”), with many common textual variants
* `Sample Filename`, which embeds GSM-specific identifiers

These differences prevent cache hits even when the semantic evidence for the 8 output fields is identical.

## Scope (minimal, deterministic)

Update the context_fingerprint normalizer with conservative rules that apply **only to fingerprinting**, not to prompts or outputs:

### 1. Ignore per-sample filename noise
Remove the line starting with:
* `Sample Filename:`

entirely from the fingerprint input.

### 2. Normalize replicate-number patterns in `Sample Title`

In the `Sample Title:` line only, normalize common replicate indicators to a canonical placeholder.

Handle the following **case-insensitive** variants:

* `rep 1`, `rep 2`, …
* `replicate 1`, `replicate 2`, …
* `rep-1`, `replicate-1`
* `rep_1`, `replicate_1`
* `Rep1`, `Rep2`
* `Replicate1`, `Replicate2`

All of the above should normalize to:

* `replicate <N>`

The rest of the title text must remain unchanged.

### Explicit non-goals

Do **not**:
* remove or normalize `Sample Characteristics` lines
* remove treatment, disease, strain, or intervention information
* change prompt content
* change any pipeline semantics

This change applies only to fingerprint generation for caching.

## Acceptance Criteria

1. Two GSM contexts differing only by:
   * GSM accession
   * `Sample Filename`
   * replicate number formatting in `Sample Title`
   produce identical `context_fingerprint`.

2. Contexts differing in semantic evidence (e.g., treatment, disease state, tumor injection) produce different fingerprints.

3. Fingerprinting remains deterministic and GSE-local.

## Required Tests

Add unit tests that verify:

1. Multiple replicate title variants normalize to the same fingerprint:
   * `rep 1`, `replicate-1`, `Rep1`, `rep_1`, etc.
2. A change in treatment or disease state produces a different fingerprint.

Run:
`uv run pytest -q`
