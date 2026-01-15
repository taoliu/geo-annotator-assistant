"""Streamlit UI for reviewing curation artifacts."""

from __future__ import annotations

import argparse
import inspect
import os
from pathlib import Path

import pandas as pd
import streamlit as st

from ui.flags import build_flags_index
from ui.help_text import (
    gsm_accession_tooltip,
    table_guidance_text,
    table_help_lines,
)
from ui.dashboard import build_dashboard_items
from ui.evidence import EVIDENCE_FIELDS, extract_field_evidence
from ui.loaders import (
    load_curation_jsonl,
    load_evidence_jsonl,
    load_suggestions_jsonl_optional,
)
from ui.overrides import (
    clear_all_overrides,
    clear_override,
    clear_overrides_for_gsm,
    compute_overrides,
    format_override_value,
    overrides_for_gsm,
    parse_override_input,
    overrides_to_jsonl,
    set_override,
)
from ui.paths import InputPaths, resolve_input_paths
from ui.schema import CANONICAL_FIELDS
from ui.state import (
    DetailsContext,
    build_details_context,
    build_table_rows,
    filter_table_rows,
    group_suggestions_by_field,
    index_curation_records,
    index_evidence_records,
    index_suggestion_records,
    resolve_selected_key,
)
from ui.styling import style_curation_table
from ui.override_safety import (
    build_override_diff,
    build_override_warning,
    field_is_editable,
    requires_override_confirmation,
)

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


def _supports_table_selection(widget: object) -> bool:
    try:
        params = inspect.signature(widget).parameters
    except (TypeError, ValueError):
        return False
    return "on_select" in params and "selection_mode" in params


def _table_column_config() -> dict[str, object]:
    column_config = getattr(st, "column_config", None)
    text_column = getattr(column_config, "TextColumn", None) if column_config else None
    if text_column is None:
        return {}
    return {"gsm_accession": text_column(help=gsm_accession_tooltip())}


def _extract_selected_rows(source: object) -> list[int]:
    if source is None:
        return []
    selection = getattr(source, "selection", None)
    if selection is None:
        if isinstance(source, dict):
            selection = source.get("selection")
    if selection is None:
        return []
    if isinstance(selection, dict):
        rows = (
            selection.get("rows")
            or selection.get("row_indices")
            or selection.get("selected_rows")
        )
    else:
        rows = getattr(selection, "rows", None) or getattr(
            selection, "row_indices", None
        )
    if rows is None:
        return []
    return list(rows)


def _render_details(
    details: DetailsContext,
    suggestions_present: bool,
    edit_mode: bool,
) -> None:
    st.subheader("Record Details")
    selection_key = details["selection_key"]
    st.caption(f"Selected: {selection_key[0]} / {selection_key[1]}")
    _render_field_status_dashboard(details)
    _render_field_override_controls(details, edit_mode)
    _render_field_evidence_panels(details)
    evidence = details["evidence"]
    suggestions = details["suggestions"]
    flagged_fields = details["flagged_fields"]

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

    curation = details["curation"]
    selected_overrides = details["selected_overrides"]
    effective_fields = details["effective_fields"]

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


def _render_field_status_dashboard(details: DetailsContext) -> None:
    st.markdown("### Field Status Dashboard")
    evidence = details["evidence"]
    items = build_dashboard_items(
        details["selection_key"],
        details["curation"],
        details["effective_fields"],
        evidence["raw"] if evidence else None,
        details["selected_overrides"],
    )
    rows = [items[:4], items[4:]]
    for row in rows:
        cols = st.columns(4)
        for idx, item in enumerate(row):
            with cols[idx]:
                st.markdown(f"**{item['label']}**")
                st.write(item["value"])
                if item["badges"]:
                    badges = " ".join(f"`{badge}`" for badge in item["badges"])
                    st.markdown(badges)
    st.markdown("---")


def _render_field_evidence_panels(details: DetailsContext) -> None:
    evidence = details["evidence"]
    evidence_raw = evidence["raw"] if evidence else None
    selection_key = details["selection_key"]
    expand_all = st.checkbox(
        "Expand all evidence",
        value=False,
        key=f"expand_all_evidence_{selection_key[0]}_{selection_key[1]}",
    )
    st.markdown("### Evidence")
    for field in EVIDENCE_FIELDS:
        items = extract_field_evidence(field, evidence_raw)
        with st.expander(f"{field} - Evidence", expanded=expand_all):
            if not items:
                st.write("(not available)")
                continue
            for item in items:
                st.write(f"{item['label']}: {item['value']}")
    st.markdown("---")


def _render_field_override_controls(details: DetailsContext, edit_mode: bool) -> None:
    st.markdown("### Field Overrides")
    selection_key = details["selection_key"]
    gse_accession, gsm_accession = selection_key
    evidence = details["evidence"]
    evidence_raw = evidence["raw"] if evidence else None
    curation = details["curation"]
    backend_fields = curation.get("fields", {}) if curation else {}
    overrides = st.session_state.get("overrides", {})
    if not isinstance(overrides, dict):
        overrides = {}
    selected_overrides = overrides_for_gsm(overrides, gse_accession, gsm_accession)

    if not edit_mode:
        st.caption("Enable editing to apply overrides.")

    for field in CANONICAL_FIELDS:
        backend_value = backend_fields.get(field)
        input_key = f"override_input_{gse_accession}_{gsm_accession}_{field}"
        diff = build_override_diff(field, backend_value, selected_overrides)
        st.markdown(f"**{field}**")
        if diff:
            st.markdown("`OVERRIDDEN`")
            st.write(f"Backend value: {diff['backend_value']}")
            st.write(f"Override value: {diff['override_value']}")
            if edit_mode and st.button(
                "Revert",
                key=f"revert_override_{gse_accession}_{gsm_accession}_{field}",
            ):
                overrides = clear_override(
                    overrides, gse_accession, gsm_accession, field
                )
                st.session_state["overrides"] = overrides
                st.session_state[input_key] = _format_override_input(backend_value)
        if not edit_mode or not field_is_editable(edit_mode, field, evidence_raw):
            continue

        warning = build_override_warning(field, evidence_raw)
        if warning:
            st.caption(warning)

        current_value = selected_overrides.get(field, backend_value)
        input_value = _format_override_input(current_value)
        if input_key not in st.session_state:
            st.session_state[input_key] = input_value
        proposed_raw = st.text_input(
            f"New value for {field}",
            value=input_value,
            key=input_key,
        )
        proposed_value = parse_override_input(proposed_raw)

        pending_key = _pending_override_key(
            gse_accession, gsm_accession, field
        )
        pending_value = st.session_state.get(pending_key)
        if pending_value is not None and pending_value != proposed_value:
            st.session_state.pop(pending_key, None)
            pending_value = None

        if st.button(
            "Apply override",
            key=f"apply_override_{gse_accession}_{gsm_accession}_{field}",
        ):
            if _override_matches_backend(backend_value, proposed_value):
                overrides = clear_override(
                    overrides, gse_accession, gsm_accession, field
                )
                st.session_state["overrides"] = overrides
                st.session_state.pop(pending_key, None)
                st.session_state[input_key] = _format_override_input(backend_value)
            elif requires_override_confirmation(field, evidence_raw):
                st.session_state[pending_key] = proposed_value
            else:
                overrides = set_override(
                    overrides, (gse_accession, gsm_accession, field), proposed_value
                )
                st.session_state["overrides"] = overrides
                st.session_state.pop(pending_key, None)

        if pending_value is not None and requires_override_confirmation(
            field, evidence_raw
        ):
            st.warning("Confirm override before applying.")
            st.write(f"Field: {field}")
            st.write(f"Backend value: {_format_override_display(backend_value)}")
            st.write(
                "Proposed override: "
                f"{_format_override_display(pending_value)}"
            )
            cols = st.columns(2)
            if cols[0].button(
                "Confirm override",
                key=f"confirm_override_{gse_accession}_{gsm_accession}_{field}",
            ):
                overrides = set_override(
                    overrides, (gse_accession, gsm_accession, field), pending_value
                )
                st.session_state["overrides"] = overrides
                st.session_state.pop(pending_key, None)
            if cols[1].button(
                "Cancel",
                key=f"cancel_override_{gse_accession}_{gsm_accession}_{field}",
            ):
                st.session_state.pop(pending_key, None)

    st.markdown("---")


def _pending_override_key(gse_accession: str, gsm_accession: str, field: str) -> str:
    return f"pending_override_{gse_accession}_{gsm_accession}_{field}"


def _format_override_input(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return format_override_value(value)
    return str(value)


def _format_override_display(value: object) -> str:
    if value is None:
        return "(not available)"
    if isinstance(value, list):
        return format_override_value(value)
    return str(value)


def _override_matches_backend(
    backend_value: object,
    override_value: object,
) -> bool:
    if isinstance(backend_value, str) and isinstance(override_value, str):
        return backend_value.strip() == override_value.strip()
    return backend_value == override_value


def _render_details_modal(
    details: DetailsContext,
    suggestions_present: bool,
    edit_mode: bool,
) -> None:
    def _body() -> None:
        if st.button("Close"):
            st.session_state["modal_open"] = False
            st.session_state["active_row_idx"] = None
        _render_details(details, suggestions_present, edit_mode)

    dialog = getattr(st, "dialog", None)
    if callable(dialog):
        try:
            with dialog("Record Details"):
                _body()
            return
        except TypeError:
            try:
                dialog("Record Details")(_body)()
                return
            except TypeError:
                pass
    with st.expander("Record Details", expanded=True):
        _body()


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
    active_row_idx = st.session_state.get("active_row_idx")
    if not isinstance(active_row_idx, int):
        active_row_idx = None
    modal_open = st.session_state.get("modal_open")
    if not isinstance(modal_open, bool):
        modal_open = False

    indicator = st.empty()

    if not filtered_rows:
        _render_unsaved_indicator(indicator, overrides)
        st.info("No records match the current filters.")
        st.stop()

    st.caption(table_guidance_text())
    with st.expander("Help"):
        for line in table_help_lines():
            st.write(line)

    column_config = _table_column_config()

    selected_rows: list[int] = []
    if edit_mode:
        action_cols = st.columns(2)
        active_selection = None
        if isinstance(active_row_idx, int):
            active_selection = resolve_selected_key(filtered_rows, [active_row_idx])
        if action_cols[0].button(
            "Revert selected row",
            disabled=active_selection is None,
        ):
            overrides = clear_overrides_for_gsm(
                overrides, active_selection[0], active_selection[1]
            )
        if action_cols[1].button("Clear all edits"):
            overrides = clear_all_overrides(overrides)

        df_base = pd.DataFrame(filtered_rows)
        df_editable = _build_editable_df(df_base, overrides, flags_by_gsm)
        st.subheader("Curation Table (Editable)")
        editor_kwargs = {
            "disabled": _disabled_columns(df_editable),
            "hide_index": True,
            "key": "curation_table_edit",
            "column_config": column_config,
        }
        if _supports_table_selection(st.data_editor):
            editor_kwargs.update(
                {"on_select": "rerun", "selection_mode": "single-row"}
            )
        df_edited = st.data_editor(df_editable, **editor_kwargs)
        selected_rows = _extract_selected_rows(
            st.session_state.get("curation_table_edit")
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
        styled = style_curation_table(df, flags_by_gsm, active_row_idx=active_row_idx)
        st.subheader("Curation Table")
        selection_event = None
        selection_supported = _supports_table_selection(st.dataframe)
        table_data = df if selection_supported else styled
        if selection_supported:
            selection_event = st.dataframe(
                table_data,
                width="stretch",
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
                column_config=column_config,
                key="curation_table_view",
            )
        else:
            st.dataframe(
                table_data,
                width="stretch",
                hide_index=True,
                column_config=column_config,
                key="curation_table_view",
            )
        selected_rows = _extract_selected_rows(
            selection_event or st.session_state.get("curation_table_view")
        )

    if selected_rows:
        row_idx = selected_rows[0]
        last_opened = st.session_state.get("last_opened_row_idx")
        if row_idx != last_opened:
            st.session_state["active_row_idx"] = row_idx
            st.session_state["modal_open"] = True
            st.session_state["last_opened_row_idx"] = row_idx
            active_row_idx = row_idx
            modal_open = True

    overrides = _render_export_section(overrides)

    curation_lookup = index_curation_records(curation_records)
    evidence_lookup = index_evidence_records(evidence_records)
    suggestions_lookup = index_suggestion_records(suggestions_records)

    if modal_open and isinstance(active_row_idx, int):
        selection_key = resolve_selected_key(filtered_rows, [active_row_idx])
        if selection_key is None:
            st.session_state["active_row_idx"] = None
            st.session_state["modal_open"] = False
        else:
            details = build_details_context(
                selection_key,
                curation_lookup,
                evidence_lookup,
                suggestions_lookup,
                flags_by_gsm,
                overrides,
            )
            _render_details_modal(details, paths.suggestions_present, edit_mode)


run_app()
