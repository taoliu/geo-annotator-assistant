# Ticket #199: Rename repository and package metadata to GEO Annotator Assistant

## Background

The upstream GitHub repository has been renamed to **GEO Annotator Assistant** and now
lives at:

- `https://github.com/taoliu/geo-annotator-assistant`

The local project metadata and Git remote should point to the new repository identity
going forward.

## Problem Statement

The local Git `origin` remote and Python package metadata still use the old
`geo-gsm-annotator-agent` repository/package name. This can cause future pushes,
package metadata inspection, and dependency lock resolution to refer to the old name.

## Proposed Change

1. Update the local GitHub remote configuration to use:
   - `https://github.com/taoliu/geo-annotator-assistant.git`
2. Update `pyproject.toml` package metadata to use the valid Python distribution name:
   - `geo-annotator-assistant`
3. Add the new GitHub repository URL to `pyproject.toml` project metadata.
4. Refresh `uv.lock` so the editable project entry reflects the new distribution name.

## Layer Affected

- [ ] Canonicalization
- [ ] Ontology grounding
- [ ] Validation / Repair
- [ ] Decision routing
- [ ] UI only
- [x] Documentation / project metadata only

## Policy Impact

- [x] No policy change
- [ ] Policy clarification only
- [ ] Policy change

This ticket changes repository/package metadata only. It must not alter annotation
semantics, schemas, validation, repair, audit, or UI authority boundaries.

## Acceptance Criteria

1. `git remote -v` shows `origin` fetch and push URLs pointing at
   `https://github.com/taoliu/geo-annotator-assistant.git`.
2. `pyproject.toml` uses `name = "geo-annotator-assistant"`.
3. `pyproject.toml` exposes the repository URL as
   `https://github.com/taoliu/geo-annotator-assistant`.
4. `uv.lock` editable project metadata uses `geo-annotator-assistant`.
5. `uv run pytest -q` passes.

## Non-Goals

- Renaming Python modules, CLI entrypoints, output schemas, or runtime artifacts.
- Updating historical milestone, checkpoint, or ticket references to the old name.
- Changing backend policy or annotation behavior.
