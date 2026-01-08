"""Streamlit UI for reviewing curation artifacts."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd
import streamlit as st

from ui.flags import build_flags_index
from ui.loaders import (
    load_curation_jsonl,
    load_evidence_jsonl,
    load_suggestions_jsonl_optional,
)
from ui.paths import InputPaths, resolve_input_paths
from ui.state import (
    build_table_rows,
    filter_table_rows,
    group_suggestions_by_field,
    index_curation_records,
    index_evidence_records,
    index_suggestion_records,
    lookup_evidence,
    lookup_suggestions,
)
from ui.styling import style_curation_table

st.set_page_config(layout="wide")


def _resolve_input_dir() -> str | None:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--input-dir")
    args, _ = parser.parse_known_args()
    if args.input_dir:
        return args.input_dir
    return os.environ.get("GEO_GSM_UI_INPUT_DIR")


def _load_records(input_dir: str) -> tuple[
    InputPaths,
    list[dict],
    list[dict],
    list[dict],
]:
    paths = resolve_input_paths(input_dir)
    curation_records = load_curation_jsonl(str(paths.curation_path))
    evidence_records = load_evidence_jsonl(str(paths.evidence_path))
    suggestions_records = load_suggestions_jsonl_optional(
        str(paths.suggestions_path)
    )
    return paths, curation_records, evidence_records, suggestions_records


def _render_header(paths: InputPaths) -> None:
    st.title("GEO GSM Curator UI")
    st.caption(f"Input directory: {paths.input_dir}")
    st.caption(f"Curation: {paths.curation_path}")
    st.caption(f"Evidence: {paths.evidence_path}")
    if paths.suggestions_present:
        st.caption(f"Suggestions: {paths.suggestions_path}")
    else:
        st.caption("Suggestions: not loaded")


def _gse_options(rows: list[dict]) -> list[str]:
    options = ["All"]
    seen: set[str] = set()
    for row in rows:
        gse = row["gse_accession"]
        if gse not in seen:
            options.append(gse)
            seen.add(gse)
    return options


def _render_filters(rows: list[dict]) -> tuple[str | None, str]:
    st.sidebar.header("Filters")
    options = _gse_options(rows)
    selected_gse = st.sidebar.selectbox("GSE", options)
    search_text = st.sidebar.text_input("Search")
    gse_filter = None if selected_gse == "All" else selected_gse
    return gse_filter, search_text


def _render_details(
    selection_key: tuple[str, str],
    curation_lookup: dict[tuple[str, str], dict],
    evidence_lookup: dict[tuple[str, str], dict],
    suggestions_lookup: dict[tuple[str, str], list[dict]],
    suggestions_present: bool,
    flags_by_gsm: dict[tuple[str, str], dict[str, list[str]]],
) -> None:
    st.subheader("Record Details")
    evidence = lookup_evidence(evidence_lookup, selection_key[0], selection_key[1])
    suggestions = lookup_suggestions(
        suggestions_lookup, selection_key[0], selection_key[1]
    )
    flagged_fields = flags_by_gsm.get(selection_key, {})

    st.caption(f"Evidence present: {'yes' if evidence else 'no'}")
    if suggestions_present:
        st.caption(f"Suggestions: {len(suggestions)}")
    else:
        st.caption("Suggestions: 0 (not loaded)")

    st.markdown("**Flags**")
    if not flagged_fields:
        st.write("None.")
    else:
        for field in sorted(flagged_fields):
            tags = ", ".join(flagged_fields[field])
            st.write(f"{field}: {tags}")

    st.markdown("**Curation (raw)**")
    curation = curation_lookup.get(selection_key)
    if curation:
        st.json(curation["raw"])
    else:
        st.write("No curation record found.")

    st.markdown("**Evidence (raw)**")
    if evidence:
        st.json(evidence["raw"])
    else:
        st.write("No evidence record found.")

    st.markdown("**Suggestions (raw)**")
    if not suggestions_present:
        st.write("Suggestions not loaded.")
        return
    if not suggestions:
        st.write("No suggestions for this GSM.")
        return
    for field, records in group_suggestions_by_field(suggestions):
        st.markdown(f"**{field}**")
        st.json([record["raw"] for record in records])


def run_app() -> None:
    input_dir = _resolve_input_dir()
    if not input_dir:
        st.error("No input directory provided. Use --input-dir or GEO_GSM_UI_INPUT_DIR.")
        st.stop()

    try:
        paths, curation_records, evidence_records, suggestions_records = _load_records(
            input_dir
        )
    except Exception as exc:
        st.error(str(exc))
        st.stop()

    _render_header(paths)

    rows = build_table_rows(curation_records)
    gse_filter, search_text = _render_filters(rows)
    filtered_rows = filter_table_rows(rows, gse_filter, search_text)

    st.caption(f"Rows: {len(filtered_rows)}")
    flags_by_gsm = build_flags_index(evidence_records)
    df = pd.DataFrame(filtered_rows)
    styled = style_curation_table(df, flags_by_gsm)
    st.subheader("Curation Table")
    st.dataframe(styled, width="stretch", hide_index=True)

    if not filtered_rows:
        st.info("No records match the current filters.")
        st.stop()

    options = [(row["gse_accession"], row["gsm_accession"]) for row in filtered_rows]
    selection = st.selectbox(
        "Select GSM",
        options,
        format_func=lambda item: f"{item[0]} / {item[1]}",
    )

    curation_lookup = index_curation_records(curation_records)
    evidence_lookup = index_evidence_records(evidence_records)
    suggestions_lookup = index_suggestion_records(suggestions_records)

    _render_details(
        selection,
        curation_lookup,
        evidence_lookup,
        suggestions_lookup,
        paths.suggestions_present,
        flags_by_gsm,
    )


run_app()
