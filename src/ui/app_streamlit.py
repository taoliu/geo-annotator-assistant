"""Streamlit UI for reviewing curation artifacts."""

from __future__ import annotations

import argparse
import csv
import json
import html
import inspect
import io
import os
from collections import Counter
from collections.abc import Mapping
from pathlib import Path
from urllib.parse import quote

import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, DataReturnMode, GridOptionsBuilder, GridUpdateMode, JsCode

from ui.flags import (
    FLAG_CATEGORY_BADGES,
    FLAG_CATEGORY_COLORS,
    FLAG_CATEGORY_LABELS,
    FLAG_CATEGORY_ORDER,
    FLAG_CATEGORY_REVIEW,
    build_curation_flags_index,
    build_flag_category_summary,
    build_flag_display_groups,
    build_flags_index,
    build_primary_failure_index,
    categorize_flag,
    extract_curation_flags,
    extract_primary_failure,
    flag_tooltip,
    format_flag_category_summary,
    primary_failure_tooltip,
)
from ui.help_text import (
    gsm_accession_tooltip,
    status_icon_tooltip,
    table_guidance_text,
)
from ui.dashboard import BADGE_TOOLTIPS, build_dashboard_items
from ui.evidence import EVIDENCE_FIELDS, extract_field_evidence
from ui.loaders import (
    load_audit_jsonl_optional,
    load_curation_jsonl,
    load_evidence_jsonl,
    load_gse_field_values_jsonl_optional,
    load_suggestions_jsonl_optional,
)
from ui.overrides import (
    apply_overrides_to_record,
    clear_all_overrides,
    clear_override,
    clear_overrides_for_gsm,
    compute_overrides,
    format_override_value,
    load_overrides_jsonl,
    overrides_for_gsm,
    parse_override_input,
    overrides_to_jsonl,
    set_override,
)
from ui.paths import InputPaths, InputScanResult, resolve_input_directory
from ui.schema import (
    CANONICAL_FIELDS,
    GSE_ACCESSION_RAW_COLUMN,
    GSM_ACCESSION_RAW_COLUMN,
)
from ui.state import (
    DetailsContext,
    TableRow,
    build_details_context,
    build_table_rows,
    filter_table_rows,
    group_suggestions_by_field,
    index_curation_records,
    index_audit_records,
    index_evidence_records,
    index_suggestion_records,
    resolve_selected_key,
)
from ui.triage import (
    TRIAGE_FILTERS,
    apply_triage_filter,
    build_triage_flags,
)
from ui.override_safety import (
    build_override_diff,
    build_override_warning,
    field_is_editable,
    requires_override_confirmation,
)

st.set_page_config(layout="wide")

STATUS_COLUMN = "Status"
GEO_ACCESSION_URL = "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc="
RAW_ACCESSION_COLUMNS = (GSE_ACCESSION_RAW_COLUMN, GSM_ACCESSION_RAW_COLUMN)
AGGRID_ROW_INDEX_COLUMN = "__row_index"
AGGRID_ROW_HAS_FLAGS_COLUMN = "__row_has_flags"
AGGRID_PRIMARY_FAILURE_COLOR_COLUMN = "__primary_failure_color"
AGGRID_FLAG_SUMMARY_COLOR_COLUMN = "__flag_summary_color"
AGGRID_TOOLTIP_FIELDS = ("gse_accession", "gsm_accession", *CANONICAL_FIELDS)
AGGRID_FLAG_FIELDS = ("data_type", "organism", "tissue_type", "cell_line", "disease")


def _inject_layout_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600&family=Fraunces:wght@500;600&display=swap');
        .stApp {
          background: radial-gradient(circle at 15% 10%, #f6f1e8 0%, #f8f7f3 45%, #ffffff 100%);
        }
        h1, h2, h3, h4 {
          font-family: 'Fraunces', serif;
          letter-spacing: -0.01em;
        }
        body, p, li, .stMarkdown, .stCaption {
          font-family: 'Space Grotesk', sans-serif;
        }
        .summary-card {
          background: linear-gradient(130deg, #fff6e9 0%, #ffffff 60%);
          border: 1px solid #f0e2cf;
          border-radius: 14px;
          padding: 12px 16px;
          margin-bottom: 8px;
        }
        .summary-label {
          font-size: 0.75rem;
          text-transform: uppercase;
          letter-spacing: 0.08em;
          color: #6b5f4b;
          margin-bottom: 4px;
        }
        .summary-value {
          font-size: 1rem;
          font-weight: 600;
          color: #2b2b2b;
        }
        .pill {
          display: inline-block;
          padding: 2px 10px;
          border-radius: 999px;
          font-size: 0.78rem;
          font-weight: 600;
          letter-spacing: 0.02em;
          border: 1px solid rgba(0,0,0,0.08);
        }
        .pill-flagged { background: #fde2e2; color: #7d2f2f; }
        .pill-accept { background: #e9f7ef; color: #1f5a3f; }
        .pill-neutral { background: #f2f2f2; color: #404040; }
        .section-divider {
          border: none;
          border-top: 1px solid #e6e0d5;
          margin: 0.4rem 0 0.5rem 0;
        }
        .gse-biology-card {
          background: #fffdfa;
          border: 1px solid #eee5d8;
          border-radius: 12px;
          padding: 10px 14px;
          margin-bottom: 8px;
        }
        .gse-biology-title {
          font-size: 0.85rem;
          text-transform: uppercase;
          letter-spacing: 0.08em;
          color: #6b5f4b;
          margin: 0;
        }
        .gse-biology-heading {
          display: flex;
          flex-direction: column;
          gap: 2px;
        }
        .gse-biology-meta {
          font-size: 0.72rem;
          color: #7b6e5b;
          letter-spacing: 0.04em;
          text-transform: uppercase;
        }
        .gse-biology-note {
          font-size: 0.72rem;
          color: #8a6b5b;
          letter-spacing: 0.02em;
        }
        .gse-biology-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 8px;
          margin: 0 0 6px 0;
        }
        .gse-biology-export {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          padding: 4px 10px;
          border-radius: 999px;
          border: 1px solid #e1d6c4;
          background: #f9f2e7;
          color: #5a4f3f;
          font-size: 0.72rem;
          font-weight: 600;
          letter-spacing: 0.03em;
          text-transform: uppercase;
          text-decoration: none;
          white-space: nowrap;
        }
        .gse-biology-export:hover {
          background: #f1e7d8;
        }
        .gse-biology-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
          gap: 6px 14px;
        }
        .gse-biology-item .label {
          font-size: 0.72rem;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          color: #7b6e5b;
        }
        .gse-biology-item .value {
          font-size: 0.92rem;
          font-weight: 600;
          color: #2b2b2b;
        }
        .gse-counts-card {
          background: #fffdfa;
          border: 1px solid #eee5d8;
          border-radius: 12px;
          padding: 10px 14px;
          margin-bottom: 8px;
        }
        .gse-counts-title {
          font-size: 0.85rem;
          text-transform: uppercase;
          letter-spacing: 0.08em;
          color: #6b5f4b;
          margin: 0 0 6px 0;
        }
        .gse-counts-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
          gap: 6px 14px;
        }
        .gse-counts-item .label {
          font-size: 0.72rem;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          color: #7b6e5b;
        }
        .gse-counts-item .value {
          font-size: 0.95rem;
          font-weight: 600;
          color: #2b2b2b;
        }
        .ag-theme-streamlit .ag-row.ag-row-has-flags .ag-cell {
          background-color: #f7f7f7;
        }
        .ag-theme-streamlit .ag-row.ag-row-selected .ag-cell {
          background-color: #e8f4ff !important;
        }
        .ag-theme-streamlit .ag-cell.ag-cell-flagged {
          background-color: #ffeaea !important;
        }
        .ag-theme-streamlit .ag-cell.ag-status-flagged {
          background-color: #fde2e2 !important;
          font-weight: 600;
          text-align: center;
        }
        .ag-theme-streamlit .ag-cell.ag-status-accept {
          background-color: #e9f7ef !important;
          font-weight: 600;
          text-align: center;
        }
        .ag-theme-streamlit .ag-cell.ag-review-bg {
          background-color: #fff4e5 !important;
        }
        .ag-theme-streamlit .ag-cell.ag-terminal-bg {
          background-color: #fde2e2 !important;
        }
        .ag-theme-streamlit .ag-cell.ag-outlier-bg {
          background-color: #fff4e5 !important;
        }
        .ag-theme-streamlit .ag-cell.ag-status-cell {
          cursor: pointer;
        }
        .ag-theme-streamlit .ag-cell.ag-geo-link {
          color: #1a73e8;
          text-decoration: underline;
          cursor: pointer;
        }
        div[data-testid="stDataFrame"] thead tr th:first-child:has(input),
        div[data-testid="stDataFrame"] tbody tr td:first-child:has(input),
        div[data-testid="stDataEditor"] thead tr th:first-child:has(input),
        div[data-testid="stDataEditor"] tbody tr td:first-child:has(input) {
          display: none;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

def _resolve_input_dir() -> str | None:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--input-dir")
    args, _ = parser.parse_known_args()
    if args.input_dir:
        return args.input_dir
    return os.environ.get("GEO_GSM_UI_INPUT_DIR")


def _load_records_for_paths(paths: InputPaths) -> tuple[
    list[dict],
    list[dict],
    list[dict],
    list[dict],
    dict | None,
    str | None,
]:
    curation_records = load_curation_jsonl(str(paths.curation_path))
    evidence_records = load_evidence_jsonl(str(paths.evidence_path))
    suggestions_records = load_suggestions_jsonl_optional(
        str(paths.suggestions_path)
    )
    audit_records: list[dict] = []
    audit_error: str | None = None
    try:
        audit_records = load_audit_jsonl_optional(str(paths.audit_path))
    except Exception as exc:
        audit_error = str(exc)
    gse_field_values = None
    if paths.gse_field_values_present:
        try:
            gse_field_values = load_gse_field_values_jsonl_optional(
                str(paths.gse_field_values_path)
            )
        except Exception as exc:
            st.warning(f"Failed to load gse_field_values.jsonl: {exc}")
    return (
        curation_records,
        evidence_records,
        suggestions_records,
        audit_records,
        gse_field_values,
        audit_error,
    )


def _resolve_inputs(input_dir: str) -> InputScanResult:
    return resolve_input_directory(input_dir)


def _render_header(
    paths: InputPaths,
    root_dir: Path | None = None,
    active_gse: str | None = None,
) -> None:
    active_title = active_gse or st.session_state.get("active_gse_label")
    if active_title:
        st.title(active_title)
    with st.expander("Input details", expanded=False):
        if root_dir and root_dir != paths.input_dir:
            st.caption(f"Input root: {root_dir}")
        st.caption(f"Input directory: {paths.input_dir}")
        st.caption(f"Curation: {paths.curation_path}")
        st.caption(f"Evidence: {paths.evidence_path}")
        if paths.suggestions_present:
            st.caption(f"Suggestions: {paths.suggestions_path}")
        else:
            st.caption("Suggestions: not loaded")
        if paths.audit_present:
            st.caption(f"Audit: {paths.audit_path}")
        else:
            st.caption("Audit: not loaded")
        if paths.gse_field_values_present:
            st.caption(f"GSE field values: {paths.gse_field_values_path}")
        else:
            st.caption("GSE field values: not loaded")
    if active_gse:
        st.session_state["active_gse_label"] = active_gse


def _section_header(title: str, subtitle: str | None = None) -> None:
    st.markdown(f"### {title}")
    if subtitle:
        st.caption(subtitle)


def _section_divider() -> None:
    st.markdown('<hr class="section-divider" />', unsafe_allow_html=True)




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


def _render_gse_switcher(
    gse_options: list[str],
    skipped: dict[str, str],
) -> str:
    st.sidebar.header("GSE Selection")
    previous = st.session_state.get("active_gse")
    active = st.sidebar.selectbox(
        "Active GSE",
        gse_options,
        index=0,
        key="active_gse",
    )
    if previous and previous != active:
        st.session_state["active_row_idx"] = None
        st.session_state["modal_open"] = False
        st.session_state["last_opened_row_idx"] = None
    if skipped:
        with st.sidebar.expander("Skipped GSE directories", expanded=False):
            for name, reason in sorted(skipped.items()):
                st.write(f"{name}: {reason}")
    return active


def _render_skipped_panel(skipped: dict[str, str]) -> None:
    if not skipped:
        return
    st.warning("Some GSE directories were skipped due to missing or invalid files.")
    with st.expander("Skipped GSE directories", expanded=False):
        for name, reason in sorted(skipped.items()):
            st.write(f"{name}: {reason}")


def _supports_table_selection(widget: object) -> bool:
    try:
        params = inspect.signature(widget).parameters
    except (TypeError, ValueError):
        return False
    return "on_select" in params and "selection_mode" in params


def _supports_column_order(widget: object) -> bool:
    try:
        params = inspect.signature(widget).parameters
    except (TypeError, ValueError):
        return False
    return "column_order" in params


def _geo_accession_url(value: object) -> str:
    if not isinstance(value, str) or not value:
        return ""
    return f"{GEO_ACCESSION_URL}{value}"


def _with_geo_links(df: pd.DataFrame, include_raw: bool = True) -> pd.DataFrame:
    if "gse_accession" not in df.columns or "gsm_accession" not in df.columns:
        return df
    if include_raw:
        if GSE_ACCESSION_RAW_COLUMN not in df.columns:
            df[GSE_ACCESSION_RAW_COLUMN] = df["gse_accession"]
        if GSM_ACCESSION_RAW_COLUMN not in df.columns:
            df[GSM_ACCESSION_RAW_COLUMN] = df["gsm_accession"]
    df["gse_accession"] = df["gse_accession"].map(_geo_accession_url)
    df["gsm_accession"] = df["gsm_accession"].map(_geo_accession_url)
    return df


def _table_column_order(df: pd.DataFrame, widget: object) -> list[str] | None:
    if not _supports_column_order(widget):
        return None
    return [column for column in df.columns if column not in RAW_ACCESSION_COLUMNS]


def _decision_icon(final_decision: str) -> str:
    normalized = final_decision.strip().upper()
    if normalized == "ACCEPT":
        return "✅"
    if normalized == "FLAGGED":
        return "🚩"
    return "—"


def _reorder_table_columns(df: pd.DataFrame) -> pd.DataFrame:
    preferred = [STATUS_COLUMN, "gse_accession", "gsm_accession", *CANONICAL_FIELDS]
    ordered = [column for column in preferred if column in df.columns]
    remainder = [column for column in df.columns if column not in ordered]
    return df[ordered + remainder]


def _table_column_config() -> dict[str, object]:
    column_config = getattr(st, "column_config", None)
    text_column = getattr(column_config, "TextColumn", None) if column_config else None
    link_column = getattr(column_config, "LinkColumn", None) if column_config else None
    if text_column is None:
        return {}
    config: dict[str, object] = {
        STATUS_COLUMN: text_column(help=status_icon_tooltip()),
    }
    if link_column is not None:
        config["gse_accession"] = link_column(
            help="Open GEO series page",
            display_text=r"acc=([A-Za-z0-9]+)",
        )
        config["gsm_accession"] = link_column(
            help="Open GEO sample page",
            display_text=r"acc=([A-Za-z0-9]+)",
        )
    else:
        config["gse_accession"] = text_column(help="GEO series accession")
        config["gsm_accession"] = text_column(help=gsm_accession_tooltip())
    return config


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


DECISION_FILTER_OPTIONS: tuple[str, ...] = (
    "All",
    "FLAGGED",
    "ACCEPT",
)

SORT_OPTIONS: tuple[str, ...] = (
    "Default (input order)",
    "Decision",
    "Review flags",
    "Primary failure",
    "Overrides",
    "Terminal fallbacks",
    "Outliers",
)


def _flag_callout(category: str):
    if category == "policy":
        return st.error
    if category == "review":
        return st.warning
    return st.info


def _render_flag_group(category: str, items: list[str]) -> None:
    if not items:
        return
    label = FLAG_CATEGORY_LABELS.get(category, category)
    badge = FLAG_CATEGORY_BADGES.get(category, category.upper())
    message = f"{badge} {label} ({len(items)})"
    _flag_callout(category)(message)
    st.markdown(_format_flag_list(items), unsafe_allow_html=True)


def _render_primary_failure(primary_failure: str) -> None:
    category = categorize_flag(primary_failure)
    label = FLAG_CATEGORY_LABELS.get(category, category)
    badge = FLAG_CATEGORY_BADGES.get(category, category.upper())
    message = f"{badge} Primary failure ({label}): {primary_failure}"
    _flag_callout(category)(message)
    st.markdown(
        _primary_failure_html(primary_failure),
        unsafe_allow_html=True,
    )


def _format_flag_list(items: list[str]) -> str:
    rendered = "".join(f"<li>{_flag_item_html(item)}</li>" for item in items)
    return (
        '<ul style="margin: 0.4em 0 0.6em 1.2em; padding: 0;">'
        + rendered
        + "</ul>"
    )


def _flag_item_html(item: str) -> str:
    tooltip = flag_tooltip(item)
    return (
        '<span title="'
        + html.escape(tooltip, quote=True)
        + '"><code>'
        + html.escape(item)
        + "</code></span>"
    )


def _primary_failure_html(primary_failure: str) -> str:
    tooltip = primary_failure_tooltip(primary_failure)
    return (
        '<div style="margin: 0.4em 0 0.6em 0;">'
        '<span title="'
        + html.escape(tooltip, quote=True)
        + '"><strong>Primary failure:</strong> <code>'
        + html.escape(primary_failure)
        + "</code></span></div>"
    )


def _row_key(row: dict) -> tuple[str, str]:
    return (row["gse_accession"], row["gsm_accession"])


def _dedupe_preserve(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if item not in seen:
            ordered.append(item)
            seen.add(item)
    return ordered


def _combine_flags(
    curation_flags: list[str],
    evidence_field_flags: dict[str, list[str]] | None,
) -> list[str]:
    combined: list[str] = []
    combined.extend(curation_flags)
    if evidence_field_flags:
        for field in CANONICAL_FIELDS:
            for flag in evidence_field_flags.get(field, []):
                combined.append(flag)
    return _dedupe_preserve(combined)


def _terminal_fallback_fields(
    curation_raw: dict | None,
    evidence_field_flags: dict[str, list[str]] | None,
) -> list[str]:
    fields: set[str] = set()
    if isinstance(curation_raw, dict):
        terminal_fields = curation_raw.get("terminal_fallback_fields")
        if isinstance(terminal_fields, list):
            for field in terminal_fields:
                if isinstance(field, str) and field:
                    fields.add(field)
    if evidence_field_flags:
        for field, flags in evidence_field_flags.items():
            if "terminal_fallback" in flags:
                fields.add(field)
    return sorted(fields)


def _outlier_categories(curation_flags: list[str]) -> list[str]:
    categories: set[str] = set()
    for flag in curation_flags:
        if flag.startswith("gse_outlier_"):
            categories.add(flag[len("gse_outlier_") :])
    return sorted(categories)


def _render_gse_summary_panel(
    rows: list[dict],
    final_decisions: dict[tuple[str, str], str],
    primary_failures: dict[tuple[str, str], str],
    combined_flags_by_gsm: dict[tuple[str, str], list[str]],
    overrides: dict,
    outlier_categories_by_gsm: dict[tuple[str, str], list[str]],
) -> None:
    total = len(rows)
    if total == 0:
        st.info("No GSMs available for summary.")
        return

    flagged = sum(
        1
        for row in rows
        if final_decisions.get(_row_key(row), "") != "ACCEPT"
    )
    flagged_fraction = flagged / total if total else 0.0
    overrides_keys = {(gse, gsm) for gse, gsm, _ in overrides}
    overrides_count = sum(1 for row in rows if _row_key(row) in overrides_keys)

    primary_counts = Counter()
    flag_counts = Counter()
    outlier_counts = Counter()
    outlier_gsm_count = 0
    for row in rows:
        key = _row_key(row)
        primary = primary_failures.get(key, "")
        if primary:
            primary_counts[primary] += 1
        for flag in combined_flags_by_gsm.get(key, []):
            flag_counts[flag] += 1
        categories = outlier_categories_by_gsm.get(key, [])
        if categories:
            outlier_gsm_count += 1
        for category in categories:
            outlier_counts[category] += 1

    st.markdown("### GSE Summary")
    cols = st.columns(4)
    cols[0].markdown(f"**Total GSMs**\n{total}")
    cols[1].markdown(
        f"**FLAGGED**\n{flagged} ({flagged_fraction:.0%})"
    )
    cols[2].markdown(f"**Overrides**\n{overrides_count}")
    cols[3].markdown(f"**Outliers**\n{outlier_gsm_count}")

    def _top_items(counter: Counter, limit: int = 5) -> str:
        if not counter:
            return "None."
        items = sorted(counter.items(), key=lambda item: (-item[1], item[0]))
        return ", ".join(f"{name} ({count})" for name, count in items[:limit])

    with st.expander("Show detailed summary", expanded=False):
        st.caption(
            f"Most common primary failures: {_top_items(primary_counts)}"
        )
        st.caption(f"Most common flags: {_top_items(flag_counts)}")
        if outlier_counts:
            st.caption(f"Outlier categories: {_top_items(outlier_counts)}")
        else:
            st.caption("Outlier categories: None.")
        st.caption("Summary reflects current GSE/search filters.")


def _render_triage_controls(
    primary_failure_options: list[str],
    flag_options: list[str],
) -> tuple[str, list[str], list[str], str, bool]:
    st.sidebar.header("Triage")
    decision_filter = st.sidebar.selectbox(
        "Decision",
        DECISION_FILTER_OPTIONS,
        index=0,
    )
    primary_filter = st.sidebar.multiselect(
        "Primary failures",
        primary_failure_options,
    )
    flag_filter = st.sidebar.multiselect(
        "Flags",
        flag_options,
    )
    sort_by = st.sidebar.selectbox(
        "Sort by",
        SORT_OPTIONS,
        index=0,
    )
    sort_desc = st.sidebar.checkbox("Sort descending", value=True)
    return decision_filter, primary_filter, flag_filter, sort_by, sort_desc


def _filter_rows_by_decision(
    rows: list[dict],
    decision_filter: str,
    final_decisions: dict[tuple[str, str], str],
) -> list[dict]:
    if decision_filter == "All":
        return rows
    filtered: list[dict] = []
    for row in rows:
        key = _row_key(row)
        if final_decisions.get(key, "") == decision_filter:
            filtered.append(row)
    return filtered


def _filter_rows_by_primary_failure(
    rows: list[dict],
    primary_filter: list[str],
    primary_failures: dict[tuple[str, str], str],
) -> list[dict]:
    if not primary_filter:
        return rows
    selected = set(primary_filter)
    return [
        row
        for row in rows
        if primary_failures.get(_row_key(row), "") in selected
    ]


def _filter_rows_by_flags(
    rows: list[dict],
    flag_filter: list[str],
    combined_flags_by_gsm: dict[tuple[str, str], list[str]],
) -> list[dict]:
    if not flag_filter:
        return rows
    selected = set(flag_filter)
    filtered: list[dict] = []
    for row in rows:
        key = _row_key(row)
        flags = combined_flags_by_gsm.get(key, [])
        if selected.intersection(flags):
            filtered.append(row)
    return filtered


def _sort_rows(
    rows: list[dict],
    sort_by: str,
    sort_desc: bool,
    final_decisions: dict[tuple[str, str], str],
    review_counts: dict[tuple[str, str], int],
    primary_failures: dict[tuple[str, str], str],
    overrides: dict,
    terminal_fallback_counts: dict[tuple[str, str], int],
    outlier_categories_by_gsm: dict[tuple[str, str], list[str]],
) -> list[dict]:
    if sort_by == "Default (input order)":
        return rows
    index_map = {_row_key(row): idx for idx, row in enumerate(rows)}
    direction = -1 if sort_desc else 1
    overrides_keys = {(gse, gsm) for gse, gsm, _ in overrides}

    def _priority(row: dict) -> int:
        key = _row_key(row)
        if sort_by == "Decision":
            return 1 if final_decisions.get(key, "") == "FLAGGED" else 0
        if sort_by == "Review flags":
            return review_counts.get(key, 0)
        if sort_by == "Primary failure":
            return 1 if primary_failures.get(key, "") else 0
        if sort_by == "Overrides":
            return 1 if key in overrides_keys else 0
        if sort_by == "Terminal fallbacks":
            return terminal_fallback_counts.get(key, 0)
        if sort_by == "Outliers":
            return 1 if outlier_categories_by_gsm.get(key) else 0
        return 0

    return sorted(
        rows,
        key=lambda row: (direction * _priority(row), index_map.get(_row_key(row), 0)),
    )


def _render_details(
    details: DetailsContext,
    suggestions_present: bool,
    edit_mode: bool,
) -> None:
    st.subheader("Record Details")
    selection_key = details["selection_key"]
    st.caption(f"Selected: {selection_key[0]} / {selection_key[1]}")
    curation = details["curation"]
    curation_raw = curation["raw"] if curation else None
    curation_flags = extract_curation_flags(curation_raw)
    primary_failure = extract_primary_failure(curation_raw)
    flagged_fields = details["flagged_fields"]
    flag_groups = build_flag_display_groups(curation_flags, flagged_fields)

    _render_decision_summary(details, curation_raw, flag_groups)
    _render_field_status_dashboard(details)
    _render_field_override_controls(details, edit_mode)
    _render_override_diff(details, curation_flags, flag_groups)
    _render_field_evidence_panels(details)
    _render_raw_artifacts(details, suggestions_present)


def _render_field_status_dashboard(details: DetailsContext) -> None:
    st.markdown("### Field Status Dashboard")
    evidence = details["evidence"]
    audit = details["audit"]
    llm_originals = _extract_llm_originals(audit["raw"] if audit else None)
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
                field = item["field"]
                backend_value = _backend_value_for_field(details, field)
                st.write(f"Backend: {backend_value}")
                llm_value = llm_originals.get(field)
                if llm_value:
                    st.caption(f"LLM original (initial proposal): {llm_value}")
                if field in details["selected_overrides"]:
                    override_value = _format_override_display(
                        details["selected_overrides"].get(field)
                    )
                    st.caption(f"Override (session): {override_value}")
                if item["badges"]:
                    st.markdown(
                        _format_badges_with_tooltips(item["badges"]),
                        unsafe_allow_html=True,
                    )
    st.markdown("---")


def _format_badges_with_tooltips(badges: list[str]) -> str:
    rendered = [_badge_html(badge) for badge in badges]
    return " ".join(rendered)


def _badge_html(badge: str) -> str:
    tooltip = BADGE_TOOLTIPS.get(
        badge, "Backend badge. Overrides remain allowed."
    )
    return (
        '<span title="'
        + html.escape(tooltip, quote=True)
        + '" style="display:inline-block; padding:2px 6px; margin-right:4px; '
        + 'border:1px solid #dcdcdc; border-radius:6px; '
        + 'font-family:monospace; font-size:0.85em; background-color:#f5f5f5;">'
        + html.escape(badge)
        + "</span>"
    )


def _render_decision_summary(
    details: DetailsContext,
    curation_raw: dict | None,
    flag_groups: dict[str, list[str]],
) -> None:
    st.markdown("### Decision Summary")
    final_decision = ""
    if isinstance(curation_raw, dict):
        final_decision = str(curation_raw.get("final_decision") or "")
    primary_failure = extract_primary_failure(curation_raw)
    overrides_count = len(details["selected_overrides"])
    evidence_present = "yes" if details["evidence"] else "no"
    suggestions_count = len(details["suggestions"])
    flagged_total = sum(len(items) for items in flag_groups.values())
    terminal_count = 0
    if isinstance(curation_raw, dict):
        terminal_fields = curation_raw.get("terminal_fallback_fields")
        if isinstance(terminal_fields, list):
            terminal_count = len(terminal_fields)

    decision_class = "pill-neutral"
    if final_decision == "FLAGGED":
        decision_class = "pill-flagged"
    elif final_decision == "ACCEPT":
        decision_class = "pill-accept"

    cols = st.columns(4)
    cols[0].markdown(
        "<div class='summary-card'>"
        "<div class='summary-label'>Decision</div>"
        f"<div class='summary-value'><span class='pill {decision_class}'>"
        f"{html.escape(final_decision or 'N/A')}</span></div></div>",
        unsafe_allow_html=True,
    )
    cols[1].markdown(
        "<div class='summary-card'>"
        "<div class='summary-label'>Primary Failure</div>"
        f"<div class='summary-value'>{_primary_failure_inline(primary_failure)}</div>"
        "</div>",
        unsafe_allow_html=True,
    )
    cols[2].markdown(
        "<div class='summary-card'>"
        "<div class='summary-label'>Flags</div>"
        f"<div class='summary-value'>{flagged_total} total</div>"
        f"<div class='summary-label'>Terminal fallbacks</div>"
        f"<div class='summary-value'>{terminal_count}</div>"
        "</div>",
        unsafe_allow_html=True,
    )
    cols[3].markdown(
        "<div class='summary-card'>"
        "<div class='summary-label'>Overrides</div>"
        f"<div class='summary-value'>{overrides_count}</div>"
        f"<div class='summary-label'>Evidence</div>"
        f"<div class='summary-value'>{html.escape(evidence_present)}</div>"
        f"<div class='summary-label'>Suggestions</div>"
        f"<div class='summary-value'>{suggestions_count}</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    st.caption("Summary-first view. Expand sections below for detail.")
    _render_flag_groups_compact(flag_groups, primary_failure)


def _primary_failure_inline(primary_failure: str) -> str:
    if not primary_failure:
        return "<span class='pill pill-neutral'>None</span>"
    tooltip = primary_failure_tooltip(primary_failure)
    return (
        "<span title=\""
        + html.escape(tooltip, quote=True)
        + "\" class='pill pill-flagged'><code>"
        + html.escape(primary_failure)
        + "</code></span>"
    )


def _render_flag_groups_compact(
    flag_groups: dict[str, list[str]],
    primary_failure: str,
    max_inline: int = 3,
) -> None:
    st.markdown("**Flag groups (compact)**")
    has_secondary = any(flag_groups.get(category) for category in FLAG_CATEGORY_ORDER)
    if not primary_failure and not has_secondary:
        st.write("None.")
        return
    if primary_failure:
        _render_primary_failure(primary_failure)
    for category in FLAG_CATEGORY_ORDER:
        items = flag_groups.get(category, [])
        if not items:
            continue
        label = FLAG_CATEGORY_LABELS.get(category, category)
        badge = FLAG_CATEGORY_BADGES.get(category, category.upper())
        message = f"{badge} {label} ({len(items)})"
        _flag_callout(category)(message)
        st.markdown(_format_flag_list(items[:max_inline]), unsafe_allow_html=True)
        if len(items) > max_inline:
            with st.expander(
                f"Show {len(items) - max_inline} more {label} flags",
                expanded=False,
            ):
                st.markdown(_format_flag_list(items[max_inline:]), unsafe_allow_html=True)


def _extract_llm_originals(audit_raw: dict | None) -> dict[str, str]:
    if not isinstance(audit_raw, dict):
        return {}
    outputs = audit_raw.get("llm_parsed_outputs")
    if not isinstance(outputs, list) or not outputs:
        return {}
    first = outputs[0]
    if not isinstance(first, dict):
        return {}
    originals: dict[str, str] = {}
    for field in (*CANONICAL_FIELDS, "gse_accession", "gsm_accession"):
        value = first.get(field)
        if value is None:
            continue
        formatted = _format_override_display(value)
        if formatted:
            originals[field] = formatted
    return originals


def _backend_value_for_field(details: DetailsContext, field: str) -> str:
    selection_key = details["selection_key"]
    if field == "gse_accession":
        return _format_override_display(selection_key[0] if selection_key else None)
    if field == "gsm_accession":
        return _format_override_display(selection_key[1] if selection_key else None)
    curation = details["curation"]
    backend_fields = curation.get("fields", {}) if curation else {}
    return _format_override_display(backend_fields.get(field))


def _render_override_diff(
    details: DetailsContext,
    curation_flags: list[str],
    flag_groups: dict[str, list[str]],
) -> None:
    selected_overrides = details["selected_overrides"]
    if not selected_overrides:
        return
    curation = details["curation"]
    backend_fields = curation.get("fields", {}) if curation else {}
    diffs: list[dict[str, str]] = []
    for field in CANONICAL_FIELDS:
        if field in selected_overrides:
            diffs.append(
                {
                    "Field": field,
                    "Backend": _format_override_display(backend_fields.get(field)),
                    "Override": _format_override_display(
                        selected_overrides.get(field)
                    ),
                }
            )
    unchanged_fields = [
        field for field in CANONICAL_FIELDS if field not in selected_overrides
    ]

    with st.expander("Override diff (backend -> override)", expanded=False):
        st.caption(
            "Overrides do not retrigger validation, repair, or ontology grounding. "
            "All backend flags remain visible for audit."
        )
        if diffs:
            st.table(diffs)
        if unchanged_fields:
            st.caption("Unchanged fields: " + ", ".join(unchanged_fields))

        st.markdown("**Signal persistence**")
        if curation_flags or any(flag_groups.values()):
            st.caption(
                "Backend flags remain active after overrides; any resolution is "
                "by human judgment only."
            )
            for category in FLAG_CATEGORY_ORDER:
                items = flag_groups.get(category, [])
                if not items:
                    continue
                label = FLAG_CATEGORY_LABELS.get(category, category)
                joined = ", ".join(items)
                st.write(f"{label}: {joined}")
        else:
            st.caption("No backend flags recorded for this GSM.")
        st.caption(
            "LOCKED and TERMINAL badges reflect backend state and are not recomputed."
        )


def _render_raw_artifacts(
    details: DetailsContext,
    suggestions_present: bool,
) -> None:
    with st.expander("Raw artifacts (advanced)", expanded=False):
        selected_overrides = details["selected_overrides"]
        effective_fields = details["effective_fields"]
        curation = details["curation"]
        evidence = details["evidence"]
        suggestions = details["suggestions"]

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
        elif not suggestions:
            st.write("No suggestions for this GSM.")
        else:
            for field, records in group_suggestions_by_field(suggestions):
                st.markdown(f"**{field}**")
                st.json([record["raw"] for record in records])


def _render_field_evidence_panels(details: DetailsContext) -> None:
    evidence = details["evidence"]
    evidence_raw = evidence["raw"] if evidence else None
    selection_key = details["selection_key"]
    with st.expander("Evidence (details)", expanded=False):
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
    st.caption(
        "Overrides do not retrigger validation, repair, or ontology grounding. "
        "Backend flags remain visible for audit."
    )
    selection_key = details["selection_key"]
    gse_accession, gsm_accession = selection_key
    evidence = details["evidence"]
    evidence_raw = evidence["raw"] if evidence else None
    curation = details["curation"]
    backend_fields = curation.get("fields", {}) if curation else {}
    overrides_by_gse = st.session_state.get("overrides_by_gse", {})
    if not isinstance(overrides_by_gse, dict):
        overrides_by_gse = {}
    overrides = overrides_by_gse.get(gse_accession, {})
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
                overrides_by_gse[gse_accession] = overrides
                st.session_state["overrides_by_gse"] = overrides_by_gse
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
                overrides_by_gse[gse_accession] = overrides
                st.session_state["overrides_by_gse"] = overrides_by_gse
                st.session_state.pop(pending_key, None)
                st.session_state[input_key] = _format_override_input(backend_value)
            elif requires_override_confirmation(field, evidence_raw):
                st.session_state[pending_key] = proposed_value
            else:
                overrides = set_override(
                    overrides, (gse_accession, gsm_accession, field), proposed_value
                )
                overrides_by_gse[gse_accession] = overrides
                st.session_state["overrides_by_gse"] = overrides_by_gse
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
                overrides_by_gse[gse_accession] = overrides
                st.session_state["overrides_by_gse"] = overrides_by_gse
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


def _tooltip_safe_value(value: object) -> str:
    formatted = _format_override_display(value)
    if formatted:
        return formatted
    return "(not available)"


def _format_confidence(value: object) -> str | None:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    return f"{numeric:.2f}"


def _format_ontology_alternate_entry(entry: Mapping[str, object]) -> str | None:
    label = entry.get("label") or entry.get("matched_label")
    term_id = entry.get("term_id") or entry.get("matched_term_id")
    source = entry.get("source") or entry.get("matched_source")
    confidence = entry.get("confidence") or entry.get("score")
    confidence_str = _format_confidence(confidence)
    parts: list[str] = []
    if term_id:
        parts.append(str(term_id))
    if source:
        parts.append(str(source))
    if confidence_str:
        parts.append(f"conf={confidence_str}")
    suffix = f" ({', '.join(parts)})" if parts else ""
    if label:
        return f"{label}{suffix}"
    if parts:
        return ", ".join(parts)
    return None


def _format_ontology_alternates(alternates: object, limit: int = 3) -> str | None:
    if not isinstance(alternates, list) or not alternates:
        return None
    formatted: list[str] = []
    for entry in alternates:
        if not isinstance(entry, Mapping):
            continue
        rendered = _format_ontology_alternate_entry(entry)
        if rendered:
            formatted.append(rendered)
        if len(formatted) >= limit:
            break
    if not formatted:
        return None
    extra = max(0, len(alternates) - len(formatted))
    if extra:
        formatted.append(f"+{extra} more")
    return "; ".join(formatted)


def _extract_ontology_alternates_by_field(
    audit_raw: Mapping[str, object] | None,
) -> dict[str, str]:
    if not isinstance(audit_raw, Mapping):
        return {}
    validation = audit_raw.get("validation")
    if not isinstance(validation, Mapping):
        return {}
    matches = validation.get("ontology_matches")
    if not isinstance(matches, Mapping):
        return {}
    alternates_by_field: dict[str, str] = {}
    for field, match in matches.items():
        if not isinstance(field, str) or field not in CANONICAL_FIELDS:
            continue
        if not isinstance(match, Mapping):
            continue
        formatted = _format_ontology_alternates(match.get("alternates"))
        if formatted:
            alternates_by_field[field] = formatted
    return alternates_by_field


def _append_aggrid_meta_columns(
    df: pd.DataFrame,
    curation_lookup: dict[tuple[str, str], dict],
    evidence_lookup: dict[tuple[str, str], dict],
    audit_lookup: dict[tuple[str, str], dict],
    flag_summaries: dict[tuple[str, str], dict[str, object]],
    primary_failures: dict[tuple[str, str], str],
) -> pd.DataFrame:
    updated = df.copy()
    records = updated.to_dict("records")

    row_indices: list[int] = []
    row_has_flags: list[bool] = []
    primary_colors: list[str] = []
    summary_colors: list[str] = []
    evidence_flag_columns: dict[str, list[list[str]]] = {
        field: [] for field in AGGRID_FLAG_FIELDS
    }
    evidence_flagged_columns: dict[str, list[bool]] = {
        field: [] for field in AGGRID_FLAG_FIELDS
    }
    evidence_attempts_columns: dict[str, list[int]] = {
        field: [] for field in AGGRID_FLAG_FIELDS
    }
    evidence_status_columns: dict[str, list[str]] = {
        field: [] for field in AGGRID_FLAG_FIELDS
    }
    evidence_terminal_columns: dict[str, list[bool]] = {
        field: [] for field in AGGRID_FLAG_FIELDS
    }

    backend_columns: dict[str, list[str]] = {
        field: [] for field in AGGRID_TOOLTIP_FIELDS
    }
    llm_columns: dict[str, list[str]] = {field: [] for field in AGGRID_TOOLTIP_FIELDS}
    ontology_columns: dict[str, list[str]] = {
        field: [] for field in AGGRID_TOOLTIP_FIELDS
    }

    for idx, row in enumerate(records):
        row_indices.append(idx)
        gse = row.get("gse_accession")
        gsm = row.get("gsm_accession")
        key = (gse, gsm) if isinstance(gse, str) and isinstance(gsm, str) else None

        evidence = evidence_lookup.get(key) if key else None
        evidence_raw = evidence.get("raw") if isinstance(evidence, dict) else None
        evidence_by_field = (
            evidence_raw.get("evidence_by_field")
            if isinstance(evidence_raw, dict)
            else None
        )

        row_flagged = False
        for field in AGGRID_FLAG_FIELDS:
            flags: list[str] = []
            attempts = 0
            status = ""
            terminal = False
            if isinstance(evidence_by_field, dict):
                field_evidence = evidence_by_field.get(field)
                if isinstance(field_evidence, dict):
                    raw_flags = field_evidence.get("flags")
                    if isinstance(raw_flags, list):
                        flags = [str(flag) for flag in raw_flags if isinstance(flag, str) and flag]
                    attempts_value = field_evidence.get("attempts", 0)
                    try:
                        attempts = int(attempts_value)
                    except (TypeError, ValueError):
                        attempts = 0
                    status_value = field_evidence.get("ontology_status")
                    if isinstance(status_value, str):
                        status = status_value
                    terminal = field_evidence.get("terminal_fallback") is True
            evidence_flag_columns[field].append(flags)
            flagged = bool(flags)
            evidence_flagged_columns[field].append(flagged)
            evidence_attempts_columns[field].append(attempts)
            evidence_status_columns[field].append(status)
            evidence_terminal_columns[field].append(terminal)
            if flagged:
                row_flagged = True

        row_has_flags.append(row_flagged)

        primary_failure = primary_failures.get(key, "") if key else ""
        if primary_failure:
            category = categorize_flag(primary_failure)
            primary_colors.append(FLAG_CATEGORY_COLORS.get(category, ""))
        else:
            primary_colors.append("")

        summary = flag_summaries.get(key) if key else None
        highest = summary.get("highest") if isinstance(summary, dict) else None
        if isinstance(highest, str) and highest:
            summary_colors.append(FLAG_CATEGORY_COLORS.get(highest, ""))
        else:
            summary_colors.append("")

        curation = curation_lookup.get(key) if key else None
        backend_fields = curation.get("fields", {}) if isinstance(curation, dict) else {}
        backend_gse = None
        backend_gsm = None
        if isinstance(curation, dict):
            backend_gse = curation.get("gse_accession")
            backend_gsm = curation.get("gsm_accession")
        if not backend_gse:
            backend_gse = gse
        if not backend_gsm:
            backend_gsm = gsm

        audit = audit_lookup.get(key) if key else None
        audit_raw = audit.get("raw") if isinstance(audit, dict) else None
        llm_originals = _extract_llm_originals(audit_raw if isinstance(audit_raw, dict) else None)
        alternates_by_field = _extract_ontology_alternates_by_field(
            audit_raw if isinstance(audit_raw, dict) else None
        )

        for field in AGGRID_TOOLTIP_FIELDS:
            if field == "gse_accession":
                backend_value = backend_gse
            elif field == "gsm_accession":
                backend_value = backend_gsm
            else:
                backend_value = backend_fields.get(field)
            backend_columns[field].append(_tooltip_safe_value(backend_value))
            llm_columns[field].append(llm_originals.get(field, ""))
            ontology_columns[field].append(alternates_by_field.get(field, ""))

    updated[AGGRID_ROW_INDEX_COLUMN] = row_indices
    updated[AGGRID_ROW_HAS_FLAGS_COLUMN] = row_has_flags
    updated[AGGRID_PRIMARY_FAILURE_COLOR_COLUMN] = primary_colors
    updated[AGGRID_FLAG_SUMMARY_COLOR_COLUMN] = summary_colors
    for field, values in evidence_flag_columns.items():
        updated[f"evidence_flags_{field}"] = values
    for field, values in evidence_flagged_columns.items():
        updated[f"__evidence_flagged_{field}"] = values
    for field, values in evidence_attempts_columns.items():
        updated[f"evidence_attempts_{field}"] = values
    for field, values in evidence_status_columns.items():
        updated[f"evidence_status_{field}"] = values
    for field, values in evidence_terminal_columns.items():
        updated[f"evidence_terminal_{field}"] = values
    for field in AGGRID_TOOLTIP_FIELDS:
        updated[f"__backend_{field}"] = backend_columns[field]
        updated[f"__llm_{field}"] = llm_columns[field]
        updated[f"__ontology_{field}"] = ontology_columns[field]

    return updated


def _evidence_flagged_fields(
    evidence_lookup: dict[tuple[str, str], dict],
    key: tuple[str, str],
) -> list[str]:
    evidence = evidence_lookup.get(key)
    evidence_raw = evidence.get("raw") if isinstance(evidence, dict) else None
    if not isinstance(evidence_raw, dict):
        return []
    evidence_by_field = evidence_raw.get("evidence_by_field")
    if not isinstance(evidence_by_field, dict):
        return []
    flagged: list[str] = []
    for field in AGGRID_FLAG_FIELDS:
        field_evidence = evidence_by_field.get(field)
        if not isinstance(field_evidence, dict):
            continue
        flags = field_evidence.get("flags")
        if isinstance(flags, list) and any(
            isinstance(flag, str) and flag for flag in flags
        ):
            flagged.append(field)
    return flagged


def _extract_aggrid_selected_rows(grid_response: dict | None) -> list[int]:
    if grid_response is None:
        return []

    selected_rows = None
    if hasattr(grid_response, "selected_rows"):
        selected_rows = grid_response.selected_rows
    elif isinstance(grid_response, Mapping):
        selected_rows = (
            grid_response.get("selected_rows")
            or grid_response.get("selectedRows")
            or grid_response.get("selected_data")
        )

    indices: list[int] = []
    if isinstance(selected_rows, pd.DataFrame):
        if AGGRID_ROW_INDEX_COLUMN in selected_rows.columns:
            raw_values = selected_rows[AGGRID_ROW_INDEX_COLUMN].tolist()
            for value in raw_values:
                if isinstance(value, int):
                    indices.append(value)
                elif isinstance(value, str) and value.isdigit():
                    indices.append(int(value))
        else:
            indices.extend([int(idx) for idx in selected_rows.index if isinstance(idx, int)])
        return indices

    if isinstance(selected_rows, list):
        for row in selected_rows:
            if not isinstance(row, dict):
                continue
            raw_index = row.get(AGGRID_ROW_INDEX_COLUMN)
            if isinstance(raw_index, int):
                indices.append(raw_index)
                continue
            if isinstance(raw_index, str) and raw_index.isdigit():
                indices.append(int(raw_index))
                continue
            node_info = row.get("_selectedRowNodeInfo")
            if isinstance(node_info, dict):
                node_index = node_info.get("nodeRowIndex")
                if isinstance(node_index, int):
                    indices.append(node_index)
    return indices


def _extract_aggrid_data(
    grid_response: dict | None,
    fallback: pd.DataFrame,
) -> pd.DataFrame:
    if grid_response is None:
        return fallback
    if hasattr(grid_response, "data"):
        data = grid_response.data
        if isinstance(data, pd.DataFrame):
            return data
        if isinstance(data, list):
            return pd.DataFrame(data)
        return fallback
    if isinstance(grid_response, Mapping):
        data = grid_response.get("data")
        if isinstance(data, pd.DataFrame):
            return data
        if isinstance(data, list):
            return pd.DataFrame(data)
    return fallback


def _aggrid_tooltip_getter(field: str, include_evidence: bool = False) -> JsCode:
    evidence_block = ""
    if include_evidence:
        evidence_block = f"""
          const attempts = params.data["evidence_attempts_{field}"];
          const attemptsValue = (attempts === null || attempts === undefined) ? "" : String(attempts);
          const status = params.data["evidence_status_{field}"] || "";
          const terminal = params.data["evidence_terminal_{field}"];
          const terminalValue = (terminal === true || terminal === "true" || terminal === "True" || terminal === 1) ? "true" : "false";
          let flagsValue = "none";
          const flags = params.data["evidence_flags_{field}"];
          if (Array.isArray(flags)) {{
            if (flags.length > 0) {{
              flagsValue = flags.join(", ");
            }}
          }} else if (typeof flags === "string") {{
            const trimmed = flags.trim();
            if (trimmed && trimmed !== "[]") {{
              flagsValue = trimmed;
            }}
          }}
          lines.push("Attempts: " + attemptsValue);
          lines.push("Ontology status: " + status);
          lines.push("Terminal fallback: " + terminalValue);
          lines.push("Evidence flags: " + flagsValue);
        """
    return JsCode(
        f"""
        function(params) {{
          const displayed = params.value;
          const displayedValue = (displayed === null || displayed === undefined || displayed === "")
            ? "(not available)"
            : String(displayed);
          const backend = params.data["__backend_{field}"] || "(not available)";
          const llm = params.data["__llm_{field}"];
          const ontology = params.data["__ontology_{field}"];
          const lines = [];
          lines.push("Displayed: " + displayedValue);
          lines.push("Backend: " + backend);
          if (llm) {{
            lines.push("LLM original: " + llm);
          }}
          if (ontology) {{
            lines.push("Ontology alternates: " + ontology);
          }}
          {evidence_block}
          return lines.join("\\n");
        }}
        """
    )


def _build_aggrid_options(df: pd.DataFrame, edit_mode: bool) -> dict:
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(
        resizable=True,
        sortable=True,
        filter=False,
        editable=False,
    )
    gb.configure_grid_options(
        suppressRowClickSelection=True,
        rowSelection="single",
        enableBrowserTooltips=True,
        tooltipShowDelay=0,
        getRowId=JsCode(
            f"function(params) {{ return params.data.{AGGRID_ROW_INDEX_COLUMN}; }}"
        ),
        rowClassRules={
            "ag-row-has-flags": f"data.{AGGRID_ROW_HAS_FLAGS_COLUMN} === true"
        },
        onCellClicked=JsCode(
            f"""
            function(event) {{
              if (event.colDef && event.colDef.field === "{STATUS_COLUMN}") {{
                event.api.deselectAll();
                event.node.setSelected(true);
                return;
              }}
              if (event.colDef && (event.colDef.field === "gse_accession" || event.colDef.field === "gsm_accession")) {{
                if (event.value) {{
                  window.open("{GEO_ACCESSION_URL}" + event.value, "_blank", "noopener,noreferrer");
                }}
              }}
            }}
            """
        ),
    )
    gb.configure_column(
        "gse_accession",
        cellClass="ag-geo-link",
        tooltipValueGetter=_aggrid_tooltip_getter("gse_accession"),
    )
    gb.configure_column(
        "gsm_accession",
        cellClass="ag-geo-link",
        tooltipValueGetter=_aggrid_tooltip_getter("gsm_accession"),
    )

    for field in CANONICAL_FIELDS:
        cell_rules = {}
        column_props: dict[str, object] = {}
        if field in AGGRID_FLAG_FIELDS:
            flag_style = JsCode(
                f"""
                function(params) {{
                  const flagged = params.data.__evidence_flagged_{field};
                  if (flagged === true || flagged === 1 || flagged === "true" || flagged === "True") {{
                    return {{ backgroundColor: "#ffeaea" }};
                  }}
                  return {{}};
                }}
                """
            )
            cell_rules["ag-cell-flagged"] = (
                f"data.__evidence_flagged_{field} === true || "
                f"data.__evidence_flagged_{field} === 'true' || "
                f"data.__evidence_flagged_{field} === 'True' || "
                f"data.__evidence_flagged_{field} === 1"
            )
            column_props["cellStyle"] = flag_style
        gb.configure_column(
            field,
            editable=edit_mode,
            tooltipValueGetter=_aggrid_tooltip_getter(
                field, include_evidence=field in AGGRID_FLAG_FIELDS
            ),
            cellClassRules=cell_rules,
            **column_props,
        )

    gb.configure_column(
        STATUS_COLUMN,
        cellClass="ag-status-cell",
        cellClassRules={
            "ag-status-flagged": f"value === '🚩'",
            "ag-status-accept": f"value === '✅'",
        },
        width=70,
    )
    gb.configure_column(
        "Review flags",
        cellClassRules={"ag-review-bg": "value !== '' && value != null"},
    )
    gb.configure_column(
        "Terminal fallbacks",
        cellClassRules={"ag-terminal-bg": "value !== '' && value != null"},
    )
    gb.configure_column(
        "Outliers",
        cellClassRules={"ag-outlier-bg": "value !== '' && value != null"},
    )

    primary_style = JsCode(
        f"""
        function(params) {{
          const color = params.data.{AGGRID_PRIMARY_FAILURE_COLOR_COLUMN};
          if (!color) {{
            return {{}};
          }}
          return {{ backgroundColor: color, fontWeight: "600" }};
        }}
        """
    )
    summary_style = JsCode(
        f"""
        function(params) {{
          const color = params.data.{AGGRID_FLAG_SUMMARY_COLOR_COLUMN};
          if (!color) {{
            return {{}};
          }}
          return {{ backgroundColor: color, fontWeight: "600" }};
        }}
        """
    )

    gb.configure_column("Primary failure", cellStyle=primary_style)
    gb.configure_column("Flag summary", cellStyle=summary_style)

    hidden_columns = [
        AGGRID_ROW_INDEX_COLUMN,
        AGGRID_ROW_HAS_FLAGS_COLUMN,
        AGGRID_PRIMARY_FAILURE_COLOR_COLUMN,
        AGGRID_FLAG_SUMMARY_COLOR_COLUMN,
    ]
    hidden_columns.extend([f"evidence_flags_{field}" for field in AGGRID_FLAG_FIELDS])
    hidden_columns.extend(
        [f"__evidence_flagged_{field}" for field in AGGRID_FLAG_FIELDS]
    )
    hidden_columns.extend(
        [f"evidence_attempts_{field}" for field in AGGRID_FLAG_FIELDS]
    )
    hidden_columns.extend(
        [f"evidence_status_{field}" for field in AGGRID_FLAG_FIELDS]
    )
    hidden_columns.extend(
        [f"evidence_terminal_{field}" for field in AGGRID_FLAG_FIELDS]
    )
    hidden_columns.extend(
        [
            "Review flags",
            "Terminal fallbacks",
            "Outliers",
            "Primary failure",
            "Flag summary",
            "flagged_fields",
        ]
    )
    for field in AGGRID_TOOLTIP_FIELDS:
        hidden_columns.append(f"__backend_{field}")
        hidden_columns.append(f"__llm_{field}")
        hidden_columns.append(f"__ontology_{field}")
    for field in hidden_columns:
        if field in df.columns:
            gb.configure_column(field, hide=True)

    return gb.build()


def _render_aggrid_table(
    df: pd.DataFrame,
    edit_mode: bool,
    key: str,
) -> dict:
    grid_options = _build_aggrid_options(df, edit_mode=edit_mode)
    update_mode = GridUpdateMode.SELECTION_CHANGED
    if edit_mode:
        update_mode = GridUpdateMode.SELECTION_CHANGED | GridUpdateMode.VALUE_CHANGED
    return AgGrid(
        df,
        gridOptions=grid_options,
        update_mode=update_mode,
        data_return_mode=DataReturnMode.AS_INPUT,
        allow_unsafe_jscode=True,
        fit_columns_on_grid_load=True,
        theme="streamlit",
        key=key,
    )


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


def _render_gse_metrics(
    total: int,
    flagged: int,
    overrides_saved: int,
    overrides_session: int,
    outliers: int,
) -> None:
    flagged_fraction = flagged / total if total else 0.0
    unsaved = max(0, overrides_session - overrides_saved)
    overrides_display = f"{overrides_saved} saved"
    if unsaved:
        overrides_display = f"{overrides_saved} saved (+{unsaved} session)"
    items = [
        ("Total GSMs", str(total)),
        ("FLAGGED", f"{flagged} ({flagged_fraction:.0%})"),
        ("Overrides", overrides_display),
        ("Outliers", str(outliers)),
    ]
    blocks = []
    for label, value in items:
        blocks.append(
            "<div class=\"gse-counts-item\">"
            f"<div class=\"label\">{html.escape(label)}</div>"
            f"<div class=\"value\">{html.escape(value)}</div>"
            "</div>"
        )
    html_block = (
        "<div class=\"gse-counts-card\">"
        "<div class=\"gse-counts-title\">"
        "GSE-wide counts (not affected by filters)"
        "</div>"
        "<div class=\"gse-counts-grid\">"
        + "".join(blocks)
        + "</div></div>"
    )
    st.markdown(html_block, unsafe_allow_html=True)

_GSE_BIOLOGY_FIELDS = ("data_type", "organism", "tissue_type", "cell_line", "disease")


def _render_gse_field_value(value: object) -> str:
    if isinstance(value, list):
        rendered = ", ".join(str(item) for item in value if item)
    else:
        rendered = str(value) if value is not None else ""
    return rendered or "—"


def _has_biology_session_edits(overrides: dict) -> bool:
    for key in overrides:
        if not isinstance(key, tuple) or len(key) < 3:
            continue
        field = key[2]
        if field in _GSE_BIOLOGY_FIELDS:
            return True
    return False


def _build_gse_biology_csv(gse_accession: str, fields: dict) -> str:
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    header = ["gse_accession", *_GSE_BIOLOGY_FIELDS]
    writer.writerow(header)
    row = [gse_accession]
    for field in _GSE_BIOLOGY_FIELDS:
        row.append(_render_gse_field_value(fields.get(field)))
    writer.writerow(row)
    return output.getvalue()


def _stringify_csv_value(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def _build_final_annotations_csv(rows: list[dict[str, object]]) -> str:
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    header = ["gse_accession", "gsm_accession", *CANONICAL_FIELDS]
    writer.writerow(header)
    for row in rows:
        writer.writerow([_stringify_csv_value(row.get(col, "")) for col in header])
    return output.getvalue()


def _render_gse_field_values_summary(
    gse_field_values: dict | None,
    has_session_edits: bool,
) -> None:
    if not isinstance(gse_field_values, dict):
        return
    fields = gse_field_values.get("fields")
    if not isinstance(fields, dict) or not fields:
        return
    preferred_fields = list(_GSE_BIOLOGY_FIELDS)
    ordered_fields = [field for field in preferred_fields if field in fields]
    extras = [field for field in fields if field not in ordered_fields]
    ordered_fields.extend(extras)

    gse_accession = gse_field_values.get("gse_accession")
    if not isinstance(gse_accession, str) or not gse_accession:
        gse_accession = "Unknown"
    csv_content = _build_gse_biology_csv(gse_accession, fields)
    csv_href = f"data:text/csv;charset=utf-8,{quote(csv_content)}"
    download_name = f"{gse_accession}_gse_wide_biology.csv"

    items: list[tuple[str, str]] = []
    for field in ordered_fields:
        rendered = _render_gse_field_value(fields.get(field))
        items.append((field, rendered))

    if not items:
        return

    blocks = []
    for field, rendered in items:
        blocks.append(
            "<div class=\"gse-biology-item\">"
            f"<div class=\"label\">{html.escape(field)}</div>"
            f"<div class=\"value\">{html.escape(rendered)}</div>"
            "</div>"
        )
    session_note = ""
    if has_session_edits:
        session_note = (
            "<div class=\"gse-biology-note\">"
            "Session edits present in biology fields."
            "</div>"
        )
    html_block = (
        "<div class=\"gse-biology-card\">"
        "<div class=\"gse-biology-header\">"
        "<div class=\"gse-biology-heading\">"
        "<div class=\"gse-biology-title\">"
        "GSE-wide biology (not affected by filters)"
        "</div>"
        "<div class=\"gse-biology-meta\">"
        "Backend-derived summary (ignores session edits)"
        "</div>"
        + session_note +
        "</div>"
        "<a class=\"gse-biology-export\" "
        f"download=\"{html.escape(download_name, quote=True)}\" "
        f"href=\"{html.escape(csv_href, quote=True)}\">"
        "Export CSV</a>"
        "</div>"
        "<div class=\"gse-biology-grid\">"
        + "".join(blocks)
        + "</div></div>"
    )
    st.markdown(html_block, unsafe_allow_html=True)


def _render_triage_filters_inline(container: st.delta_generator.DeltaGenerator) -> str:
    container.markdown("**Quick filter:**")
    return container.radio(
        "Table filter",
        TRIAGE_FILTERS,
        index=0,
        horizontal=True,
        label_visibility="collapsed",
        key="triage_filter",
    )


def _build_editable_df(
    df_base: pd.DataFrame,
    overrides: dict,
    evidence_lookup: dict[tuple[str, str], dict],
    flags_by_gsm: dict[tuple[str, str], dict[str, list[str]]],
    flag_summaries: dict[tuple[str, str], dict[str, object]],
    primary_failures: dict[tuple[str, str], str],
    final_decisions: dict[tuple[str, str], str],
    review_counts: dict[tuple[str, str], int],
    terminal_fallback_counts: dict[tuple[str, str], int],
    outlier_categories_by_gsm: dict[tuple[str, str], list[str]],
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
    status_values = [
        _decision_icon(
            final_decisions.get((row["gse_accession"], row["gsm_accession"]), "")
        )
        for row in df_base.to_dict("records")
    ]
    df_editable[STATUS_COLUMN] = status_values
    df_editable["Edited"] = edited_values

    review_values = []
    terminal_values = []
    outlier_values = []
    primary_values = []
    summary_values = []
    for row in df_base.to_dict("records"):
        key = (row["gse_accession"], row["gsm_accession"])
        review_count = review_counts.get(key, 0)
        review_values.append(str(review_count) if review_count else "")
        terminal_count = terminal_fallback_counts.get(key, 0)
        terminal_values.append(str(terminal_count) if terminal_count else "")
        outliers = outlier_categories_by_gsm.get(key, [])
        outlier_values.append(",".join(outliers))
        primary_values.append(primary_failures.get(key, ""))
        summary = flag_summaries.get(key)
        if summary is None:
            summary = build_flag_category_summary([], {})
        summary_values.append(format_flag_category_summary(summary))
    df_editable["Review flags"] = review_values
    df_editable["Terminal fallbacks"] = terminal_values
    df_editable["Outliers"] = outlier_values
    df_editable["Primary failure"] = primary_values
    df_editable["Flag summary"] = summary_values

    flagged_values = []
    for row in df_base.to_dict("records"):
        key = (row["gse_accession"], row["gsm_accession"])
        flagged = _evidence_flagged_fields(evidence_lookup, key)
        flagged_values.append(",".join(sorted(flagged)))
    df_editable["flagged_fields"] = flagged_values
    return _reorder_table_columns(df_editable)


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


def _overrides_path(active_paths: InputPaths) -> Path:
    return active_paths.input_dir / "overrides.jsonl"


def _ensure_saved_overrides(
    gse_accession: str,
    active_paths: InputPaths,
) -> tuple[dict, dict, bool]:
    overrides_by_gse = st.session_state.get("overrides_by_gse", {})
    if not isinstance(overrides_by_gse, dict):
        overrides_by_gse = {}
    saved_by_gse = st.session_state.get("saved_overrides_by_gse", {})
    if not isinstance(saved_by_gse, dict):
        saved_by_gse = {}

    path = _overrides_path(active_paths)
    saved_present = path.is_file()
    if gse_accession not in saved_by_gse:
        if saved_present:
            try:
                saved_by_gse[gse_accession] = load_overrides_jsonl(
                    str(path), gse_accession
                )
            except Exception as exc:
                st.warning(
                    f"Failed to load overrides.jsonl for {gse_accession}: {exc}"
                )
                saved_by_gse[gse_accession] = {}
        else:
            saved_by_gse[gse_accession] = {}
    if gse_accession not in overrides_by_gse:
        overrides_by_gse[gse_accession] = dict(saved_by_gse[gse_accession])

    st.session_state["overrides_by_gse"] = overrides_by_gse
    st.session_state["saved_overrides_by_gse"] = saved_by_gse
    return overrides_by_gse, saved_by_gse, saved_present


def _render_overrides_persistence(
    active_paths: InputPaths,
    gse_accession: str,
    overrides: dict,
    saved_overrides: dict,
    saved_present: bool,
) -> dict:
    st.subheader("Overrides (persistent)")
    edited_gsms = {(gse, gsm) for gse, gsm, _ in overrides}
    st.write(f"Edited GSMs: {len(edited_gsms)}")
    st.write(f"Edited fields: {len(overrides)}")
    if saved_present:
        st.success("Saved overrides detected (loaded from disk).")
    else:
        st.info("No saved overrides found for this GSE.")

    has_unsaved = overrides != saved_overrides
    if has_unsaved:
        st.warning("Unsaved edits (session differs from disk).")
    else:
        st.caption("Session matches saved overrides.")

    cols = st.columns(3)
    if cols[0].button("Save overrides"):
        lines: list[str] = []
        try:
            lines = overrides_to_jsonl(overrides)
        except ValueError as exc:
            st.error(str(exc))
            lines = []
        if lines:
            path = _overrides_path(active_paths)
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            st.success(f"Saved overrides to {path}.")
            saved_overrides = dict(overrides)
            saved_present = True
        else:
            st.info("No overrides to save.")

    if cols[1].button("Revert to saved"):
        overrides = dict(saved_overrides)
        st.info("Reverted to saved overrides.")

    discard_confirm = st.checkbox(
        "Confirm discard saved overrides",
        key=f"confirm_discard_overrides_{gse_accession}",
    )
    if cols[2].button("Discard saved overrides"):
        if not discard_confirm:
            st.warning("Please confirm discard before deleting saved overrides.")
        else:
            path = _overrides_path(active_paths)
            try:
                if path.exists():
                    path.unlink()
                saved_overrides = {}
                saved_present = False
                st.success("Saved overrides deleted.")
            except OSError as exc:
                st.error(f"Failed to delete overrides: {exc}")

    overrides_by_gse = st.session_state.get("overrides_by_gse", {})
    if not isinstance(overrides_by_gse, dict):
        overrides_by_gse = {}
    overrides_by_gse[gse_accession] = overrides
    st.session_state["overrides_by_gse"] = overrides_by_gse
    saved_by_gse = st.session_state.get("saved_overrides_by_gse", {})
    if not isinstance(saved_by_gse, dict):
        saved_by_gse = {}
    saved_by_gse[gse_accession] = saved_overrides
    st.session_state["saved_overrides_by_gse"] = saved_by_gse
    return overrides


def _render_export_final_annotations(
    curation_records: list[dict],
    overrides: dict,
) -> None:
    st.subheader("Exports")
    st.caption(
        "Exports apply curator overrides but do not rerun validation, repair, "
        "or ontology grounding."
    )

    def _final_annotation_rows() -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        for record in curation_records:
            gse = record["gse_accession"]
            gsm = record["gsm_accession"]
            selected = overrides_for_gsm(overrides, gse, gsm)
            effective_fields = apply_overrides_to_record(record, selected)
            if effective_fields is None:
                continue
            output = {
                "gse_accession": gse,
                "gsm_accession": gsm,
                "data_type": effective_fields.get("data_type", ""),
                "organism": effective_fields.get("organism", ""),
                "tissue_type": effective_fields.get("tissue_type", ""),
                "cell_line": effective_fields.get("cell_line", ""),
                "disease": effective_fields.get("disease", ""),
                "treatment": effective_fields.get("treatment", ""),
            }
            rows.append(output)
        return rows

    rows = _final_annotation_rows()
    lines = [json.dumps(row) for row in rows]
    preview = "\n".join(lines)
    gse_accession = "Unknown"
    if curation_records:
        candidate = curation_records[0].get("gse_accession")
        if isinstance(candidate, str) and candidate:
            gse_accession = candidate
    csv_content = _build_final_annotations_csv(rows)
    st.text_area(
        "Preview (annotations.final.jsonl)",
        value=preview,
        height=200,
        disabled=True,
    )
    export_cols = st.columns(2)
    export_cols[0].download_button(
        "Export final annotations",
        data=preview,
        file_name="annotations.final.jsonl",
        mime="application/jsonl",
        disabled=not rows,
    )
    export_cols[1].download_button(
        "Export final annotations as CSV",
        data=csv_content,
        file_name=f"{gse_accession}_final_annotations.csv",
        mime="text/csv",
        disabled=not rows,
    )


def run_app() -> None:
    _inject_layout_styles()
    input_dir = _resolve_input_dir()
    if not input_dir:
        st.error("No input directory provided. Use --input-dir or GEO_GSM_UI_INPUT_DIR.")
        st.stop()

    try:
        inputs = _resolve_inputs(input_dir)
    except Exception as exc:
        st.error(str(exc))
        st.stop()

    active_paths: InputPaths
    if inputs.mode == "multi":
        gse_options = sorted(inputs.gse_paths.keys())
        active_gse = _render_gse_switcher(gse_options, inputs.skipped)
        active_paths = inputs.gse_paths[active_gse]
    else:
        active_gse = None
        active_paths = inputs.single_paths if inputs.single_paths else None
        if active_paths is None:
            st.error("No valid input directory found.")
            st.stop()

    try:
        (
            curation_records,
            evidence_records,
            suggestions_records,
            audit_records,
            gse_field_values,
            audit_error,
        ) = _load_records_for_paths(active_paths)
    except Exception as exc:
        st.error(str(exc))
        st.stop()

    if audit_error:
        st.warning(
            "audit.jsonl could not be loaded; continuing without LLM originals. "
            f"Details: {audit_error}"
        )

    _render_header(
        active_paths,
        root_dir=inputs.input_dir,
        active_gse=active_gse,
    )
    if inputs.mode == "multi":
        _render_skipped_panel(inputs.skipped)

    rows = build_table_rows(curation_records)
    gse_filter, search_text, edit_mode = _render_filters(rows)
    base_rows = filter_table_rows(rows, gse_filter, search_text)

    flags_by_gsm = build_flags_index(evidence_records)
    curation_flags_by_gsm = build_curation_flags_index(curation_records)
    primary_failures = build_primary_failure_index(curation_records)
    flag_summaries: dict[tuple[str, str], dict[str, object]] = {}
    final_decisions: dict[tuple[str, str], str] = {}
    combined_flags_by_gsm: dict[tuple[str, str], list[str]] = {}
    review_counts: dict[tuple[str, str], int] = {}
    terminal_fallback_counts: dict[tuple[str, str], int] = {}
    outlier_categories_by_gsm: dict[tuple[str, str], list[str]] = {}
    for record in curation_records:
        key = (record["gse_accession"], record["gsm_accession"])
        curation_raw = record.get("raw", {})
        final_decisions[key] = (
            curation_raw.get("final_decision") if isinstance(curation_raw, dict) else ""
        ) or ""
        summary = build_flag_category_summary(
            curation_flags_by_gsm.get(key, []),
            flags_by_gsm.get(key, {}),
        )
        flag_summaries[key] = summary
        counts = summary.get("counts") if isinstance(summary, dict) else {}
        review_counts[key] = int(counts.get(FLAG_CATEGORY_REVIEW, 0)) if isinstance(counts, dict) else 0
        evidence_field_flags = flags_by_gsm.get(key, {})
        combined_flags_by_gsm[key] = _combine_flags(
            curation_flags_by_gsm.get(key, []),
            evidence_field_flags,
        )
        terminal_fallback_counts[key] = len(
            _terminal_fallback_fields(curation_raw, evidence_field_flags)
        )
        outlier_categories_by_gsm[key] = _outlier_categories(
            curation_flags_by_gsm.get(key, [])
        )
    evidence_lookup = index_evidence_records(evidence_records)
    curation_lookup = index_curation_records(curation_records)
    audit_lookup = index_audit_records(audit_records)
    gse_id = active_gse
    if not gse_id:
        if curation_records:
            gse_id = curation_records[0]["gse_accession"]
        else:
            gse_id = active_paths.input_dir.name
    overrides_by_gse, saved_by_gse, saved_present = _ensure_saved_overrides(
        gse_id,
        active_paths,
    )
    overrides = overrides_by_gse.get(gse_id, {})
    saved_overrides = saved_by_gse.get(gse_id, {})
    active_row_idx = st.session_state.get("active_row_idx")
    if not isinstance(active_row_idx, int):
        active_row_idx = None
    modal_open = st.session_state.get("modal_open")
    if not isinstance(modal_open, bool):
        modal_open = False

    indicator = st.empty()

    triage_flags = build_triage_flags(base_rows, evidence_lookup, overrides)
    saved_override_keys = {(gse, gsm) for gse, gsm, _ in saved_overrides}
    session_override_keys = {(gse, gsm) for gse, gsm, _ in overrides}
    flagged_count = sum(
        1 for decision in final_decisions.values() if decision != "ACCEPT"
    )
    outlier_count = sum(
        1 for categories in outlier_categories_by_gsm.values() if categories
    )
    has_biology_edits = _has_biology_session_edits(overrides)
    _render_gse_field_values_summary(gse_field_values, has_biology_edits)
    _render_gse_metrics(
        total=len(rows),
        flagged=flagged_count,
        overrides_saved=len(saved_override_keys),
        overrides_session=len(session_override_keys),
        outliers=outlier_count,
    )
    _section_divider()
    header_cols = st.columns([3, 5])
    header_cols[0].markdown("### Curation table")
    triage_filter = _render_triage_filters_inline(header_cols[1])
    primary_failure_options = sorted(
        {
            primary_failures.get(_row_key(row), "")
            for row in base_rows
            if primary_failures.get(_row_key(row), "")
        }
    )
    flag_options = sorted(
        {
            flag
            for row in base_rows
            for flag in combined_flags_by_gsm.get(_row_key(row), [])
        }
    )
    (
        decision_filter,
        primary_filter,
        flag_filter,
        sort_by,
        sort_desc,
    ) = _render_triage_controls(primary_failure_options, flag_options)
    filtered_rows = apply_triage_filter(base_rows, triage_flags, triage_filter)
    filtered_rows = _filter_rows_by_decision(
        filtered_rows, decision_filter, final_decisions
    )
    filtered_rows = _filter_rows_by_primary_failure(
        filtered_rows, primary_filter, primary_failures
    )
    filtered_rows = _filter_rows_by_flags(
        filtered_rows, flag_filter, combined_flags_by_gsm
    )
    filtered_rows = _sort_rows(
        filtered_rows,
        sort_by,
        sort_desc,
        final_decisions,
        review_counts,
        primary_failures,
        overrides,
        terminal_fallback_counts,
        outlier_categories_by_gsm,
    )
    st.caption(f"Rows: {len(filtered_rows)}")

    if not filtered_rows:
        _render_unsaved_indicator(indicator, overrides)
        st.info("No records match the current filters.")
        st.stop()
    st.caption(table_guidance_text())

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
            overrides_by_gse[gse_id] = overrides
            st.session_state["overrides_by_gse"] = overrides_by_gse
        if action_cols[1].button("Clear all edits"):
            overrides = clear_all_overrides(overrides)
            overrides_by_gse[gse_id] = overrides
            st.session_state["overrides_by_gse"] = overrides_by_gse

        df_base = pd.DataFrame(filtered_rows)
        df_editable = _build_editable_df(
            df_base,
            overrides,
            evidence_lookup,
            flags_by_gsm,
            flag_summaries,
            primary_failures,
            final_decisions,
            review_counts,
            terminal_fallback_counts,
            outlier_categories_by_gsm,
        )
        df_editable = _append_aggrid_meta_columns(
            df_editable,
            curation_lookup,
            evidence_lookup,
            audit_lookup,
            flag_summaries,
            primary_failures,
        )
        grid_response = _render_aggrid_table(
            df_editable,
            edit_mode=True,
            key="curation_table_edit",
        )
        selected_rows = _extract_aggrid_selected_rows(grid_response)
        df_edited = _extract_aggrid_data(grid_response, df_editable)
        overrides_visible = compute_overrides(df_base, df_edited)
        visible_keys = {
            (row["gse_accession"], row["gsm_accession"]) for row in filtered_rows
        }
        overrides = _merge_overrides(overrides, overrides_visible, visible_keys)
        overrides_by_gse[gse_id] = overrides
        st.session_state["overrides_by_gse"] = overrides_by_gse
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
            status_values = [
                _decision_icon(
                    final_decisions.get((row["gse_accession"], row["gsm_accession"]), "")
                )
                for row in filtered_rows
            ]
            df[STATUS_COLUMN] = status_values
            df["Edited"] = edited_values
            review_values = []
            terminal_values = []
            outlier_values = []
            primary_values = []
            summary_values = []
            for row in filtered_rows:
                key = (row["gse_accession"], row["gsm_accession"])
                review_count = review_counts.get(key, 0)
                review_values.append(str(review_count) if review_count else "")
                terminal_count = terminal_fallback_counts.get(key, 0)
                terminal_values.append(str(terminal_count) if terminal_count else "")
                outliers = outlier_categories_by_gsm.get(key, [])
                outlier_values.append(",".join(outliers))
                primary_values.append(primary_failures.get(key, ""))
                summary = flag_summaries.get(key)
                if summary is None:
                    summary = build_flag_category_summary([], {})
                summary_values.append(format_flag_category_summary(summary))
            df["Review flags"] = review_values
            df["Terminal fallbacks"] = terminal_values
            df["Outliers"] = outlier_values
            df["Primary failure"] = primary_values
            df["Flag summary"] = summary_values
            flagged_values = []
            for row in filtered_rows:
                key = (row["gse_accession"], row["gsm_accession"])
                flagged = _evidence_flagged_fields(evidence_lookup, key)
                flagged_values.append(",".join(sorted(flagged)))
            df["flagged_fields"] = flagged_values
            df = _reorder_table_columns(df)
        if not df.empty:
            df = _append_aggrid_meta_columns(
                df,
                curation_lookup,
                evidence_lookup,
                audit_lookup,
                flag_summaries,
                primary_failures,
            )
            grid_response = _render_aggrid_table(
                df,
                edit_mode=False,
                key="curation_table_view",
            )
            selected_rows = _extract_aggrid_selected_rows(grid_response)

    if selected_rows:
        row_idx = selected_rows[0]
        last_opened = st.session_state.get("last_opened_row_idx")
        if row_idx != last_opened:
            st.session_state["active_row_idx"] = row_idx
            st.session_state["modal_open"] = True
            st.session_state["last_opened_row_idx"] = row_idx
            active_row_idx = row_idx
            modal_open = True

    overrides = _render_overrides_persistence(
        active_paths,
        gse_id,
        overrides,
        saved_overrides,
        saved_present,
    )
    _render_export_final_annotations(curation_records, overrides)

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
                audit_lookup,
                suggestions_lookup,
                flags_by_gsm,
                overrides,
            )
            _render_details_modal(details, active_paths.suggestions_present, edit_mode)


run_app()
