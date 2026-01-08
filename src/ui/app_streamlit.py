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
from ui.overrides import (
    apply_overrides_to_record,
    clear_all_overrides,
    clear_overrides_for_gsm,
    compute_overrides,
    format_override_value,
    overrides_for_gsm,
    overrides_to_jsonl,
)
from ui.paths import InputPaths, resolve_input_paths
from ui.schema import CANONICAL_FIELDS
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


def _render_filters(rows: list[dict]) -> tuple[str | None, str, bool]:
    st.sidebar.header("Filters")
    options = _gse_options(rows)
    selected_gse = st.sidebar.selectbox("GSE", options)
    search_text = st.sidebar.text_input("Search")
    edit_mode = st.sidebar.checkbox("Enable editing", value=False)
    gse_filter = None if selected_gse == "All" else selected_gse
    return gse_filter, search_text, edit_mode


def _render_details(
    selection_key: tuple[str, str],
    curation_lookup: dict[tuple[str, str], dict],
    evidence_lookup: dict[tuple[str, str], dict],
    suggestions_lookup: dict[tuple[str, str], list[dict]],
    suggestions_present: bool,
    flags_by_gsm: dict[tuple[str, str], dict[str, list[str]]],
    overrides: dict,
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

    curation = curation_lookup.get(selection_key)
    selected_overrides = overrides_for_gsm(overrides, selection_key[0], selection_key[1])
    effective_fields = apply_overrides_to_record(curation, selected_overrides)

    st.markdown("**Overrides (in-memory)**")
    if not selected_overrides:
        st.write("None.")
    else:
        st.json(selected_overrides)

    st.markdown("**Curation (effective)**")
    if effective_fields:
        st.json(effective_fields)
    else:
        st.write("No curation record found.")

    st.markdown("**Curation (raw)**")
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


def _render_unsaved_indicator(container: st.delta_generator.DeltaGenerator, overrides: dict) -> None:
    if not overrides:
        container.empty()
        return
    edited_gsms = {(gse, gsm) for gse, gsm, _ in overrides}
    container.info(
        "Unsaved edits (session-only). "
        f"Edited GSMs: {len(edited_gsms)}. "
        f"Edited fields: {len(overrides)}."
    )


def _build_editable_df(
    df_base: pd.DataFrame,
    overrides: dict,
    flags_by_gsm: dict[tuple[str, str], dict[str, list[str]]],
) -> pd.DataFrame:
    df_editable = df_base.copy()
    for (gse, gsm, field), value in overrides.items():
        if field not in CANONICAL_FIELDS:
            continue
        mask = (df_editable["gse_accession"] == gse) & (
            df_editable["gsm_accession"] == gsm
        )
        if mask.any():
            df_editable.loc[mask, field] = format_override_value(value)

    edited_keys = {(gse, gsm) for gse, gsm, _ in overrides}
    edited_values = [
        "Yes" if (row["gse_accession"], row["gsm_accession"]) in edited_keys else ""
        for row in df_base.to_dict("records")
    ]
    df_editable.insert(2, "Edited", edited_values)

    flagged_values = []
    for row in df_base.to_dict("records"):
        flagged = flags_by_gsm.get((row["gse_accession"], row["gsm_accession"]), {})
        flagged_values.append(",".join(sorted(flagged)))
    df_editable["flagged_fields"] = flagged_values
    return df_editable


def _disabled_columns(df: pd.DataFrame) -> list[str]:
    return [column for column in df.columns if column not in CANONICAL_FIELDS]


def _merge_overrides(
    existing: dict,
    overrides_visible: dict,
    visible_keys: set[tuple[str, str]],
) -> dict:
    merged = {
        key: value
        for key, value in existing.items()
        if (key[0], key[1]) not in visible_keys
    }
    merged.update(overrides_visible)
    return merged


def _render_export_section(overrides: dict) -> dict:
    st.subheader("Overrides export (session-only edits)")
    edited_gsms = {(gse, gsm) for gse, gsm, _ in overrides}
    st.write(f"Edited GSMs: {len(edited_gsms)}")
    st.write(f"Edited fields: {len(overrides)}")
    if not overrides:
        st.write("No edits to export.")

    lines: list[str] = []
    if overrides:
        try:
            lines = overrides_to_jsonl(overrides)
        except ValueError as exc:
            st.error(str(exc))

    preview = "\n".join(lines)
    st.text_area("Preview (JSONL)", value=preview, height=200, disabled=True)

    cols = st.columns(2)
    downloaded = cols[0].download_button(
        "Export overrides.jsonl",
        data=preview,
        file_name="overrides.jsonl",
        mime="application/jsonl",
        disabled=not lines,
    )
    clear_clicked = cols[1].button("Cancel / Clear edits")
    if downloaded:
        st.success("Overrides ready for download.")
    if clear_clicked:
        overrides = clear_all_overrides(overrides)
        st.session_state["overrides"] = overrides
    return overrides


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
    gse_filter, search_text, edit_mode = _render_filters(rows)
    filtered_rows = filter_table_rows(rows, gse_filter, search_text)

    st.caption(f"Rows: {len(filtered_rows)}")
    flags_by_gsm = build_flags_index(evidence_records)
    overrides = st.session_state.get("overrides", {})
    if not isinstance(overrides, dict):
        overrides = {}

    indicator = st.empty()

    if not filtered_rows:
        _render_unsaved_indicator(indicator, overrides)
        st.info("No records match the current filters.")
        st.stop()

    options = [(row["gse_accession"], row["gsm_accession"]) for row in filtered_rows]
    selection = st.selectbox(
        "Select GSM",
        options,
        format_func=lambda item: f"{item[0]} / {item[1]}",
    )

    if edit_mode:
        action_cols = st.columns(2)
        if action_cols[0].button("Revert selected row"):
            overrides = clear_overrides_for_gsm(
                overrides, selection[0], selection[1]
            )
        if action_cols[1].button("Clear all edits"):
            overrides = clear_all_overrides(overrides)

        df_base = pd.DataFrame(filtered_rows)
        df_editable = _build_editable_df(df_base, overrides, flags_by_gsm)
        st.subheader("Curation Table (Editable)")
        df_edited = st.data_editor(
            df_editable,
            disabled=_disabled_columns(df_editable),
            hide_index=True,
        )
        overrides_visible = compute_overrides(df_base, df_edited)
        visible_keys = {
            (row["gse_accession"], row["gsm_accession"]) for row in filtered_rows
        }
        overrides = _merge_overrides(overrides, overrides_visible, visible_keys)
        st.session_state["overrides"] = overrides
        _render_unsaved_indicator(indicator, overrides)
    else:
        _render_unsaved_indicator(indicator, overrides)
        df = pd.DataFrame(filtered_rows)
        if not df.empty:
            edited_keys = {(gse, gsm) for gse, gsm, _ in overrides}
            edited_values = [
                "Yes" if (row["gse_accession"], row["gsm_accession"]) in edited_keys else ""
                for row in filtered_rows
            ]
            df.insert(2, "Edited", edited_values)
        styled = style_curation_table(df, flags_by_gsm)
        st.subheader("Curation Table")
        st.dataframe(styled, width="stretch", hide_index=True)

    overrides = _render_export_section(overrides)

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
        overrides,
    )


run_app()
