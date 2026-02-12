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
from datetime import datetime, timezone
from collections.abc import Mapping
from pathlib import Path
from urllib.parse import quote

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from st_aggrid import AgGrid, DataReturnMode, GridOptionsBuilder, GridUpdateMode, JsCode

from agent import summarize_cli
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
    bulk_edit_tooltip,
    gsm_accession_tooltip,
    status_icon_tooltip,
    table_guidance_text,
    table_legend_tooltip,
)
from ui.checked import merge_visible_checked_updates
from ui.dashboard import BADGE_TOOLTIPS, build_dashboard_items
from ui.evidence import EVIDENCE_FIELDS, extract_field_evidence
from ui.gse_navigation import ensure_active_gse, step_active_gse
from ui.bulk_edit import (
    apply_bulk_edit,
    build_bulk_edit_preview,
    build_bulk_edit_samples,
    is_empty_bulk_value,
    normalize_selected_rows,
    resolve_selected_keys,
    validate_bulk_edit,
)
from ui.bulk_mode import (
    activate_bulk_mode,
    is_bulk_mode_active,
    reset_bulk_mode_state,
)
from ui.loaders import (
    load_audit_jsonl_optional,
    load_curation_jsonl,
    load_evidence_jsonl,
    load_gse_field_values_jsonl_optional,
    load_suggestions_jsonl_optional,
)
from ui.overrides import (
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
from ui.triage_state import merge_options_with_selected, normalize_triage_state
from ui.override_safety import (
    build_override_diff,
    build_override_warning,
    field_is_editable,
    requires_override_confirmation,
)

st.set_page_config(layout="wide")

STATUS_COLUMN = "Status"
CHECKED_COLUMN = "checked"
EDITED_COLUMN = "Edited"
EDITED_BOOL_COLUMN = "is_edited"
EDITED_ICON = "✏️"
GEO_ACCESSION_URL = "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc="
RAW_ACCESSION_COLUMNS = (GSE_ACCESSION_RAW_COLUMN, GSM_ACCESSION_RAW_COLUMN)
AGGRID_ROW_INDEX_COLUMN = "__row_index"
AGGRID_ROW_HAS_FLAGS_COLUMN = "__row_has_flags"
AGGRID_PRIMARY_FAILURE_COLOR_COLUMN = "__primary_failure_color"
AGGRID_FLAG_SUMMARY_COLOR_COLUMN = "__flag_summary_color"
AGGRID_TOOLTIP_FIELDS = ("gse_accession", "gsm_accession", *CANONICAL_FIELDS)
AGGRID_FLAG_FIELDS = CANONICAL_FIELDS
BULK_EDIT_SAMPLE_LIMIT = 8


def _inject_layout_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600&family=Fraunces:wght@500;600&display=swap');
        .stApp {
          background: radial-gradient(circle at 15% 10%, #f6f1e8 0%, #f8f7f3 45%, #ffffff 100%);
        }
        div[data-testid="stAppViewContainer"] > .main .block-container {
          padding-top: 0.5rem;
        }
        section[data-testid="stSidebar"] div[data-testid="stSidebarContent"] {
          padding-top: 0.3rem;
        }
        section[data-testid="stSidebar"] .block-container {
          padding-top: 0.1rem;
        }
        div[data-testid="stAppViewContainer"] h1 {
          margin-top: 0.1rem;
        }
        .stExpander,
        div[data-testid="stExpander"] {
          margin-top: -0.5rem;
          margin-bottom: -0.25rem;
        }
        .stExpander details:not([open]) > summary,
        div[data-testid="stExpander"] details:not([open]) > summary {
          padding-top: -0.5rem;
          padding-bottom: -0.25rem;
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
          font-size: 0.3rem;
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
          font-size: 0.4rem;
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
          margin: 0.2rem 0 0.25rem 0;
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
          outline: 1px solid #4f6f90 !important;
          outline-offset: -1px;
        }
        .ag-theme-streamlit .ag-row.ag-row-selected .ag-cell:first-child {
          border-left: 3px solid #355a7d !important;
        }
        .ag-theme-streamlit .ag-cell.ag-cell-flagged {
          background-color: #ffe7cc !important;
        }
        .ag-theme-streamlit .ag-cell.ag-cell-overridden {
          background-color: #dff4df !important;
        }
        .ag-theme-streamlit .ag-cell.ag-cell-overridden-flagged {
          background-color: #dff4df !important;
          box-shadow: inset 0 0 0 2px #e47b00 !important;
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
          cursor: default;
          text-align: center;
        }
        .ag-theme-streamlit .ag-cell.ag-checked-cell {
          text-align: center;
        }
        .ag-theme-streamlit .ag-cell.ag-edited-cell {
          text-align: center;
        }
        .ag-theme-streamlit .ag-cell.ag-geo-link {
          color: #1a73e8;
          text-decoration: underline;
          cursor: pointer;
        }
        .diag-tooltip {
          max-width: 430px;
          background: #ffffff;
          border: 1px solid #d9dee8;
          border-radius: 10px;
          box-shadow: 0 8px 20px rgba(15, 23, 42, 0.18);
          padding: 8px 10px;
          font-size: 0.76rem;
          line-height: 1.35;
          color: #1f2937;
        }
        .diag-tooltip-group + .diag-tooltip-group {
          margin-top: 7px;
          padding-top: 7px;
          border-top: 1px solid #e7ebf3;
        }
        .diag-tooltip-group-title {
          margin: 0 0 4px 0;
          font-size: 0.63rem;
          text-transform: uppercase;
          letter-spacing: 0.06em;
          color: #6b7280;
          font-weight: 600;
        }
        .diag-tooltip-row {
          display: flex;
          align-items: flex-start;
          gap: 6px;
          margin: 2px 0;
        }
        .diag-tooltip-key {
          display: inline-block;
          background: #e9f1ff;
          border: 1px solid #d3def3;
          color: #334155;
          border-radius: 999px;
          padding: 1px 7px;
          font-size: 0.66rem;
          font-weight: 600;
          line-height: 1.3;
          white-space: nowrap;
        }
        .diag-tooltip-value {
          color: inherit;
          overflow-wrap: anywhere;
          word-break: break-word;
        }
        @media (prefers-color-scheme: dark) {
          .diag-tooltip {
            background: #111827;
            border-color: #3a455a;
            color: #e5e7eb;
            box-shadow: 0 10px 24px rgba(0, 0, 0, 0.45);
          }
          .diag-tooltip-group + .diag-tooltip-group {
            border-top-color: #374151;
          }
          .diag-tooltip-group-title {
            color: #9ca3af;
          }
          .diag-tooltip-key {
            background: #1f2937;
            border-color: #475569;
            color: #d1d5db;
          }
        }
        .inline-help-icon {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          width: 1.1rem;
          height: 1.1rem;
          border-radius: 999px;
          border: 1px solid #d9cbb6;
          background: #fffaf2;
          color: #665743;
          font-size: 0.75rem;
          line-height: 1;
          cursor: help;
          margin-left: 0.25rem;
          user-select: none;
        }
        .bulk-preview-card {
          background: linear-gradient(130deg, #f9f3e8 0%, #ffffff 70%);
          border: 1px solid #e7d8c1;
          border-radius: 12px;
          padding: 10px 12px;
          margin: 6px 0 8px 0;
        }
        .bulk-preview-title {
          font-size: 0.8rem;
          text-transform: uppercase;
          letter-spacing: 0.08em;
          color: #6b5f4b;
          margin: 0 0 6px 0;
          font-weight: 600;
        }
        .bulk-preview-grid {
          display: grid;
          grid-template-columns: repeat(2, minmax(160px, 1fr));
          gap: 6px 16px;
        }
        .bulk-preview-item .label {
          font-size: 0.72rem;
          text-transform: uppercase;
          letter-spacing: 0.04em;
          color: #7b6e5b;
        }
        .bulk-preview-item .value {
          font-size: 0.92rem;
          font-weight: 600;
          color: #2b2b2b;
          word-break: break-word;
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
    active_gse: str | None = None,
) -> None:
    active_title = active_gse or st.session_state.get("active_gse_label")
    if active_title:
        st.title(active_title)
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


def _render_filters(rows: list[dict]) -> tuple[str | None, str]:
    st.sidebar.markdown("### Filters")
    options = _gse_options(rows)
    selected_gse = st.sidebar.selectbox("GSE", options)
    search_text = st.sidebar.text_input(
        "Search",
        help="Matches accession text and visible field text.",
    )
    st.sidebar.markdown("---")
    gse_filter = None if selected_gse == "All" else selected_gse
    return gse_filter, search_text


def _render_gse_switcher(
    gse_options: list[str],
    skipped: dict[str, str],
) -> str:
    st.sidebar.header("GSE Selection")
    state_key = "active_gse"
    pending_target = st.session_state.pop("active_gse_nav_target", None)
    previous = ensure_active_gse(st.session_state.get(state_key), gse_options)
    if isinstance(pending_target, str) and pending_target in gse_options:
        previous = pending_target
    st.session_state[state_key] = previous

    active = st.sidebar.selectbox(
        "Active GSE",
        gse_options,
        key=state_key,
        help="Use ↑ / ↓ to navigate GSEs",
    )
    resolved_index = gse_options.index(active)
    nav_cols = st.sidebar.columns(2)
    prev_clicked = nav_cols[0].button(
        "◀ Prev",
        key="active_gse_prev",
        disabled=resolved_index <= 0,
    )
    next_clicked = nav_cols[1].button(
        "Next ▶",
        key="active_gse_next",
        disabled=resolved_index >= (len(gse_options) - 1),
    )
    if prev_clicked:
        next_active = step_active_gse(active, gse_options, "prev")
        if next_active != active:
            st.session_state["active_gse_nav_target"] = next_active
            st.session_state["active_row_idx"] = None
            _request_rerun()
            return next_active
    if next_clicked:
        next_active = step_active_gse(active, gse_options, "next")
        if next_active != active:
            st.session_state["active_gse_nav_target"] = next_active
            st.session_state["active_row_idx"] = None
            _request_rerun()
            return next_active
    if previous and previous != active:
        st.session_state["active_row_idx"] = None
    if skipped:
        with st.sidebar.expander("Skipped GSE directories", expanded=False):
            for name, reason in sorted(skipped.items()):
                st.write(f"{name}: {reason}")
    _inject_active_gse_scroll_script()
    return active


def _inject_active_gse_scroll_script() -> None:
    components.html(
        """
        <script>
        (function() {
          const doc = window.parent && window.parent.document ? window.parent.document : null;
          if (!doc) return;
          const sidebar = doc.querySelector('section[data-testid="stSidebar"]');
          if (!sidebar) return;

          const selectboxes = sidebar.querySelectorAll('div[data-testid="stSelectbox"]');
          let activeBox = null;
          for (const box of selectboxes) {
            const label = box.querySelector('label');
            const text = label ? (label.textContent || "") : "";
            if (text.indexOf("Active GSE") >= 0) {
              activeBox = box;
              break;
            }
          }
          if (!activeBox) return;

          const combobox = activeBox.querySelector('[role="combobox"]');
          if (!combobox) return;
          if (combobox.dataset.gseScrollBound === "1") return;
          combobox.dataset.gseScrollBound = "1";

          const centerSelected = function() {
            window.setTimeout(function() {
              const options = doc.querySelectorAll('[role="option"]');
              let selected = null;
              for (const option of options) {
                if (option.getAttribute('aria-selected') === 'true') {
                  selected = option;
                  break;
                }
              }
              if (selected && typeof selected.scrollIntoView === "function") {
                selected.scrollIntoView({ block: "center" });
              }
            }, 40);
          };

          combobox.addEventListener('mousedown', centerSelected);
          combobox.addEventListener('keydown', function(evt) {
            const isExpanded = combobox.getAttribute("aria-expanded") === "true";
            if (!isExpanded && !evt.repeat && (evt.key === "ArrowDown" || evt.key === "ArrowUp")) {
              const buttons = sidebar.querySelectorAll("button");
              let prevButton = null;
              let nextButton = null;
              for (const button of buttons) {
                const text = (button.textContent || "").trim();
                if (text === "◀ Prev GSE") prevButton = button;
                if (text === "Next GSE ▶") nextButton = button;
              }
              if (evt.key === "ArrowDown" && nextButton) {
                evt.preventDefault();
                evt.stopPropagation();
                nextButton.click();
                return;
              }
              if (evt.key === "ArrowUp" && prevButton) {
                evt.preventDefault();
                evt.stopPropagation();
                prevButton.click();
                return;
              }
            }
            if (evt.key === 'Enter' || evt.key === ' ' || evt.key === 'ArrowDown') {
              centerSelected();
            }
          });
        })();
        </script>
        """,
        height=0,
        width=0,
    )


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
    preferred = [
        STATUS_COLUMN,
        CHECKED_COLUMN,
        EDITED_COLUMN,
        "gse_accession",
        "gsm_accession",
        *CANONICAL_FIELDS,
    ]
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

TRIAGE_DECISION_KEY = "triage_decision_filter"
TRIAGE_PRIMARY_KEY = "triage_primary_filter"
TRIAGE_FLAG_KEY = "triage_flag_filter"
TRIAGE_SORT_KEY = "triage_sort_by"
TRIAGE_SORT_DESC_KEY = "triage_sort_desc"
TRIAGE_STATE_KEY = "triage_state"


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
    st.sidebar.markdown("### Triage")
    persisted_state = normalize_triage_state(
        st.session_state.get(TRIAGE_STATE_KEY),
        decision_options=DECISION_FILTER_OPTIONS,
        sort_options=SORT_OPTIONS,
    )

    decision_existing = st.session_state.get(TRIAGE_DECISION_KEY)
    if (
        not isinstance(decision_existing, str)
        or decision_existing not in DECISION_FILTER_OPTIONS
    ):
        st.session_state[TRIAGE_DECISION_KEY] = persisted_state["decision"]
    primary_existing = st.session_state.get(TRIAGE_PRIMARY_KEY)
    if not isinstance(primary_existing, list):
        st.session_state[TRIAGE_PRIMARY_KEY] = list(persisted_state["primary"])
    else:
        st.session_state[TRIAGE_PRIMARY_KEY] = normalize_triage_state(
            {"primary": primary_existing},
            decision_options=DECISION_FILTER_OPTIONS,
            sort_options=SORT_OPTIONS,
        )["primary"]
    flag_existing = st.session_state.get(TRIAGE_FLAG_KEY)
    if not isinstance(flag_existing, list):
        st.session_state[TRIAGE_FLAG_KEY] = list(persisted_state["flags"])
    else:
        st.session_state[TRIAGE_FLAG_KEY] = normalize_triage_state(
            {"flags": flag_existing},
            decision_options=DECISION_FILTER_OPTIONS,
            sort_options=SORT_OPTIONS,
        )["flags"]
    sort_existing = st.session_state.get(TRIAGE_SORT_KEY)
    if not isinstance(sort_existing, str) or sort_existing not in SORT_OPTIONS:
        st.session_state[TRIAGE_SORT_KEY] = persisted_state["sort_by"]
    if not isinstance(st.session_state.get(TRIAGE_SORT_DESC_KEY), bool):
        st.session_state[TRIAGE_SORT_DESC_KEY] = bool(persisted_state["sort_desc"])

    decision_filter = st.sidebar.selectbox(
        "Decision",
        DECISION_FILTER_OPTIONS,
        key=TRIAGE_DECISION_KEY,
    )
    primary_filter = st.sidebar.multiselect(
        "Primary failures",
        merge_options_with_selected(
            primary_failure_options,
            st.session_state.get(TRIAGE_PRIMARY_KEY, []),
        ),
        key=TRIAGE_PRIMARY_KEY,
    )
    flag_filter = st.sidebar.multiselect(
        "Flags",
        merge_options_with_selected(
            flag_options,
            st.session_state.get(TRIAGE_FLAG_KEY, []),
        ),
        key=TRIAGE_FLAG_KEY,
    )
    st.sidebar.markdown("**Sort**")
    sort_by = st.sidebar.selectbox(
        "Sort by",
        SORT_OPTIONS,
        key=TRIAGE_SORT_KEY,
    )
    sort_desc = st.sidebar.checkbox("Sort descending", key=TRIAGE_SORT_DESC_KEY)
    st.sidebar.markdown("---")
    normalized_state = normalize_triage_state(
        {
            "decision": decision_filter,
            "primary": primary_filter,
            "flags": flag_filter,
            "sort_by": sort_by,
            "sort_desc": sort_desc,
        },
        decision_options=DECISION_FILTER_OPTIONS,
        sort_options=SORT_OPTIONS,
    )
    st.session_state[TRIAGE_STATE_KEY] = normalized_state
    return (
        str(normalized_state["decision"]),
        list(normalized_state["primary"]),
        list(normalized_state["flags"]),
        str(normalized_state["sort_by"]),
        bool(normalized_state["sort_desc"]),
    )


def _render_table_debug_toggle() -> bool:
    with st.sidebar.expander("Advanced", expanded=False):
        return st.checkbox(
            "Debug table wiring",
            value=False,
            key="debug_table_wiring",
        )


def _render_table_debug(
    enabled: bool,
    grid_version: int,
    table_df: pd.DataFrame,
) -> None:
    if not enabled:
        return
    edited_count = 0
    if EDITED_BOOL_COLUMN in table_df.columns:
        edited_count = int(table_df[EDITED_BOOL_COLUMN].sum())
    st.sidebar.markdown("**Table debug**")
    st.sidebar.caption(f"grid_version: {grid_version}")
    st.sidebar.caption(f"table_df id: {id(table_df)}")
    st.sidebar.caption(f"is_edited true: {edited_count}")


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


def _help_icon_html(tooltip: str) -> str:
    safe = html.escape(tooltip, quote=True).replace("\n", " ")
    return (
        "<span "
        "class=\"inline-help-icon\" "
        "tabindex=\"0\" "
        "role=\"img\" "
        f"aria-label=\"{safe}\" "
        f"title=\"{safe}\">"
        "ⓘ"
        "</span>"
    )


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


def _extract_ontology_alternates_from_match(
    match: Mapping[str, object] | None,
) -> str | None:
    if not isinstance(match, Mapping):
        return None
    for key in ("alternates", "ontology_alternates", "candidates", "match_candidates"):
        formatted = _format_ontology_alternates(match.get(key))
        if formatted:
            return formatted
    return None


def _extract_ontology_alternates_from_matches_map(
    matches: Mapping[str, object] | None,
) -> dict[str, str]:
    if not isinstance(matches, Mapping):
        return {}
    alternates_by_field: dict[str, str] = {}
    for field, match in matches.items():
        if not isinstance(field, str) or field not in CANONICAL_FIELDS:
            continue
        formatted = _extract_ontology_alternates_from_match(
            match if isinstance(match, Mapping) else None
        )
        if formatted:
            alternates_by_field[field] = formatted
    return alternates_by_field


def _extract_ontology_alternates_by_field(
    audit_raw: Mapping[str, object] | None,
    curation_raw: Mapping[str, object] | None = None,
    evidence_raw: Mapping[str, object] | None = None,
) -> dict[str, str]:
    # Primary source: audit.validation.ontology_matches
    audit_validation = audit_raw.get("validation") if isinstance(audit_raw, Mapping) else None
    audit_matches = (
        audit_validation.get("ontology_matches")
        if isinstance(audit_validation, Mapping)
        else None
    )
    alternates_by_field = _extract_ontology_alternates_from_matches_map(
        audit_matches if isinstance(audit_matches, Mapping) else None
    )

    # Fallback source: curation.raw.validation.ontology_matches or curation.raw.ontology_matches
    if isinstance(curation_raw, Mapping):
        curation_validation = curation_raw.get("validation")
        curation_matches = (
            curation_validation.get("ontology_matches")
            if isinstance(curation_validation, Mapping)
            else curation_raw.get("ontology_matches")
        )
        curation_alternates = _extract_ontology_alternates_from_matches_map(
            curation_matches if isinstance(curation_matches, Mapping) else None
        )
        for field, value in curation_alternates.items():
            alternates_by_field.setdefault(field, value)

    # Fallback source: evidence.raw.evidence_by_field[*].(ontology_alternates|alternates|candidates)
    evidence_by_field = (
        evidence_raw.get("evidence_by_field")
        if isinstance(evidence_raw, Mapping)
        else None
    )
    if isinstance(evidence_by_field, Mapping):
        for field in CANONICAL_FIELDS:
            if field in alternates_by_field:
                continue
            field_evidence = evidence_by_field.get(field)
            if not isinstance(field_evidence, Mapping):
                continue
            formatted = _extract_ontology_alternates_from_match(field_evidence)
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
        curation_raw = curation.get("raw") if isinstance(curation, dict) else None
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
            audit_raw if isinstance(audit_raw, Mapping) else None,
            curation_raw if isinstance(curation_raw, Mapping) else None,
            evidence_raw if isinstance(evidence_raw, Mapping) else None,
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


def _row_selection_id_from_row(row: Mapping[str, object]) -> str | None:
    gse = row.get("gse_accession")
    gsm = row.get("gsm_accession")
    if isinstance(gse, str) and isinstance(gsm, str) and (gse or gsm):
        return f"{gse}::{gsm}"
    raw_index = row.get(AGGRID_ROW_INDEX_COLUMN)
    if isinstance(raw_index, int):
        return str(raw_index)
    if isinstance(raw_index, str) and raw_index:
        return raw_index
    return None


def _extract_aggrid_selected_rows(
    grid_response: dict | None,
    table_df: pd.DataFrame | None = None,
) -> list[int]:
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
    if indices:
        return indices

    grid_state = None
    if hasattr(grid_response, "grid_state"):
        grid_state = grid_response.grid_state
    elif isinstance(grid_response, Mapping):
        grid_state = (
            grid_response.get("grid_state")
            or grid_response.get("gridState")
        )
    if not isinstance(grid_state, Mapping):
        return indices
    selected_ids = grid_state.get("rowSelection")
    if not isinstance(selected_ids, list) or not selected_ids:
        return indices
    if not isinstance(table_df, pd.DataFrame):
        return indices

    id_to_index: dict[str, int] = {}
    for row in table_df.to_dict("records"):
        if not isinstance(row, dict):
            continue
        row_id = _row_selection_id_from_row(row)
        if not isinstance(row_id, str):
            continue
        row_index = row.get(AGGRID_ROW_INDEX_COLUMN)
        if isinstance(row_index, int):
            id_to_index[row_id] = row_index
        elif isinstance(row_index, str) and row_index.isdigit():
            id_to_index[row_id] = int(row_index)

    for selected_id in selected_ids:
        if not isinstance(selected_id, str):
            continue
        mapped = id_to_index.get(selected_id)
        if isinstance(mapped, int):
            indices.append(mapped)
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
          entries.push({{ key: "Attempts", value: attemptsValue }});
          entries.push({{ key: "Ontology status", value: status }});
          entries.push({{ key: "Terminal fallback", value: terminalValue }});
          entries.push({{ key: "Evidence flags", value: flagsValue }});
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
          const entries = [];
          entries.push({{ key: "Displayed", value: displayedValue }});
          entries.push({{ key: "Backend", value: backend }});
          if (llm) {{
            entries.push({{ key: "LLM original", value: llm }});
          }}
          if (ontology) {{
            entries.push({{ key: "Ontology alternates", value: ontology }});
          }}
          {evidence_block}
          return {{ entries: entries }};
        }}
        """
    )


def _aggrid_accession_tooltip_getter() -> JsCode:
    return JsCode(
        """
        function() {
          return { plain_message: "Click this accession number to go to GEO website" };
        }
        """
    )


def _aggrid_diagnostics_tooltip_component() -> JsCode:
    return JsCode(
        """
        (function() {
          function clamp(value, minValue, maxValue) {
            return Math.min(Math.max(value, minValue), maxValue);
          }

          function viewportSize() {
            var doc = document.documentElement || {};
            return {
              width: Math.max(doc.clientWidth || 0, window.innerWidth || 0),
              height: Math.max(doc.clientHeight || 0, window.innerHeight || 0),
            };
          }

          function resolveCellRect(params) {
            if (
              params &&
              params.eGridCell &&
              typeof params.eGridCell.getBoundingClientRect === "function"
            ) {
              return params.eGridCell.getBoundingClientRect();
            }
            if (!params) {
              return null;
            }
            var api = params.api;
            var column = params.column;
            var rowIndex = params.rowIndex;
            var colId = (
              column &&
              typeof column.getColId === "function"
            ) ? column.getColId() : null;
            if (
              api &&
              typeof api.getGui === "function" &&
              typeof rowIndex === "number" &&
              typeof colId === "string" &&
              colId
            ) {
              var gridGui = api.getGui();
              if (gridGui && typeof gridGui.querySelectorAll === "function") {
                var rowSelector = '.ag-row[row-index="' + String(rowIndex) + '"]';
                var rowElements = gridGui.querySelectorAll(rowSelector);
                for (var i = 0; i < rowElements.length; i += 1) {
                  var rowEl = rowElements[i];
                  var cells = rowEl.querySelectorAll(".ag-cell[col-id]");
                  for (var j = 0; j < cells.length; j += 1) {
                    var cell = cells[j];
                    if (cell.getAttribute("col-id") === colId) {
                      return cell.getBoundingClientRect();
                    }
                  }
                }
              }
            }
            return null;
          }

          function resolvePopupElement(root) {
            if (!root) {
              return null;
            }
            if (typeof root.closest === "function") {
              var popupWrapper = root.closest(".ag-popup");
              if (popupWrapper) {
                return popupWrapper;
              }
              var tooltipWrapper = root.closest(".ag-tooltip");
              if (tooltipWrapper) {
                return tooltipWrapper;
              }
            }
            if (
              root.parentElement &&
              root.parentElement.classList &&
              root.parentElement.classList.contains("ag-tooltip")
            ) {
              return root.parentElement;
            }
            return root;
          }

          function placeTooltip(params, root) {
            if (!root) {
              return;
            }
            window.requestAnimationFrame(function() {
              var popupEl = resolvePopupElement(root);
              if (!popupEl) {
                return;
              }
              var cellRect = resolveCellRect(params);
              if (!cellRect) {
                return;
              }
              var gap = 10;
              var margin = 8;
              var topOffset = 2;
              var viewport = viewportSize();
              var baseMaxWidth = Math.min(
                430,
                Math.max(180, viewport.width - (margin * 2))
              );
              var minFallbackWidth = 120;

              popupEl.style.position = "fixed";
              popupEl.style.pointerEvents = "none";
              popupEl.style.zIndex = "10000";
              popupEl.style.transform = "none";
              popupEl.style.margin = "0";
              root.style.maxWidth = String(baseMaxWidth) + "px";

              var availableRight = viewport.width - cellRect.right - margin;
              var availableLeft = cellRect.left - margin;
              var preferredTop = cellRect.top + topOffset;
              var columnLeft = cellRect.left;
              var columnRight = cellRect.right;

              function measureForWidth(maxWidthValue) {
                var safeWidth = Math.max(1, Math.floor(maxWidthValue));
                root.style.maxWidth = String(safeWidth) + "px";
                popupEl.style.left = "0px";
                popupEl.style.top = "0px";
                return {
                  width: Math.ceil(popupEl.offsetWidth || root.offsetWidth || 0),
                  height: Math.ceil(popupEl.offsetHeight || root.offsetHeight || 0),
                };
              }

              function intersectsHoveredColumn(left, width) {
                var tooltipRight = left + width;
                var paddedColumnLeft = columnLeft - 1;
                var paddedColumnRight = columnRight + 1;
                return !(
                  tooltipRight <= paddedColumnLeft || left >= paddedColumnRight
                );
              }

              function trySide(side) {
                var sideCap = side === "right"
                  ? (availableRight - gap)
                  : (availableLeft - gap);
                if (sideCap <= 0) {
                  return null;
                }
                var size = measureForWidth(Math.min(baseMaxWidth, sideCap));
                if (!size.width || !size.height) {
                  return null;
                }
                if (size.width > sideCap) {
                  return null;
                }
                var proposedLeft = side === "right"
                  ? (columnRight + gap)
                  : (columnLeft - size.width - gap);
                if (intersectsHoveredColumn(proposedLeft, size.width)) {
                  return null;
                }
                return {
                  left: proposedLeft,
                  top: preferredTop,
                  width: size.width,
                  height: size.height,
                  side: side,
                };
              }

              var placement = trySide("right") || trySide("left");

              if (!placement) {
                var fallbackSide = availableLeft >= availableRight ? "left" : "right";
                var fallbackCap = fallbackSide === "right"
                  ? (availableRight - gap)
                  : (availableLeft - gap);
                var fallbackWidth = Math.min(
                  baseMaxWidth,
                  Math.max(minFallbackWidth, fallbackCap)
                );
                var fallbackSize = measureForWidth(fallbackWidth);
                if (!fallbackSize.width || !fallbackSize.height) {
                  return;
                }
                var verticalTop = preferredTop;
                var belowTop = cellRect.bottom + gap;
                var aboveTop = cellRect.top - fallbackSize.height - gap;
                var hasBelowSpace = (viewport.height - cellRect.bottom - margin) >= (fallbackSize.height + gap);
                var hasAboveSpace = (cellRect.top - margin) >= (fallbackSize.height + gap);
                if (hasBelowSpace) {
                  verticalTop = belowTop;
                } else if (hasAboveSpace) {
                  verticalTop = aboveTop;
                }
                placement = {
                  left: fallbackSide === "right"
                    ? (columnRight + gap)
                    : (columnLeft - fallbackSize.width - gap),
                  top: verticalTop,
                  width: fallbackSize.width,
                  height: fallbackSize.height,
                  side: fallbackSide,
                };
              }

              var maxLeft = Math.max(margin, viewport.width - placement.width - margin);
              var maxTop = Math.max(margin, viewport.height - placement.height - margin);
              var finalLeft = clamp(placement.left, margin, maxLeft);
              var finalTop = clamp(placement.top, margin, maxTop);

              if (intersectsHoveredColumn(finalLeft, placement.width)) {
                var rightCandidate = columnRight + gap;
                var leftCandidate = columnLeft - placement.width - gap;
                var rightFits = (rightCandidate + placement.width) <= (viewport.width - margin);
                var leftFits = leftCandidate >= margin;
                if (rightFits && !intersectsHoveredColumn(rightCandidate, placement.width)) {
                  finalLeft = rightCandidate;
                } else if (leftFits && !intersectsHoveredColumn(leftCandidate, placement.width)) {
                  finalLeft = leftCandidate;
                }
              }

              popupEl.style.left = String(clamp(finalLeft, margin, maxLeft)) + "px";
              popupEl.style.top = String(finalTop) + "px";
              popupEl.style.visibility = "visible";
            });
          }

          function normalizeEntries(value) {
            if (value && Array.isArray(value.entries)) {
              return value.entries
                .filter(function(item) {
                  return item && typeof item.key === "string";
                })
                .map(function(item) {
                  return {
                    key: item.key,
                    value: item.value === null || item.value === undefined ? "" : String(item.value),
                  };
                });
            }
            if (typeof value === "string" && value) {
              return value.split("\\n").map(function(line) {
                var idx = line.indexOf(":");
                if (idx < 0) {
                  return { key: line, value: "" };
                }
                return {
                  key: line.slice(0, idx).trim(),
                  value: line.slice(idx + 1).trim(),
                };
              });
            }
            return [];
          }

          function groupName(key) {
            if (key === "Displayed" || key === "Backend" || key === "LLM original") {
              return "Values";
            }
            if (key === "Ontology alternates" || key === "Ontology status") {
              return "Ontology";
            }
            if (key === "Attempts" || key === "Terminal fallback") {
              return "Repair / fallback";
            }
            if (key === "Evidence flags") {
              return "Evidence";
            }
            return "";
          }

          function Tooltip() {}

          Tooltip.prototype.init = function(params) {
            this.params = params || null;
            var root = document.createElement("div");
            root.className = "diag-tooltip";
            var darkMode = !!(
              window.matchMedia &&
              window.matchMedia("(prefers-color-scheme: dark)").matches
            );
            root.style.maxWidth = "430px";
            root.style.background = darkMode ? "#111827" : "#ffffff";
            root.style.border = "1px solid " + (darkMode ? "#3a455a" : "#d9dee8");
            root.style.borderRadius = "10px";
            root.style.boxShadow = darkMode
              ? "0 10px 24px rgba(0, 0, 0, 0.45)"
              : "0 8px 20px rgba(15, 23, 42, 0.18)";
            root.style.padding = "8px 10px";
            root.style.fontSize = "0.76rem";
            root.style.lineHeight = "1.35";
            root.style.color = darkMode ? "#e5e7eb" : "#1f2937";
            var tooltipValue = params ? params.value : null;
            if (
              tooltipValue &&
              typeof tooltipValue === "object" &&
              typeof tooltipValue.plain_message === "string" &&
              tooltipValue.plain_message
            ) {
              root.textContent = tooltipValue.plain_message;
              this.eGui = root;
              return;
            }
            var entries = normalizeEntries(tooltipValue);
            if (!entries.length) {
              root.textContent = "(not available)";
              this.eGui = root;
              return;
            }

            var groups = {};
            var order = [];
            entries.forEach(function(entry) {
              var key = groupName(entry.key);
              if (!groups[key]) {
                groups[key] = [];
                order.push(key);
              }
              groups[key].push(entry);
            });

            order.forEach(function(groupKey, groupIndex) {
              var section = document.createElement("div");
              section.className = "diag-tooltip-group";
              if (groupIndex > 0) {
                section.style.marginTop = "7px";
                section.style.paddingTop = "7px";
                section.style.borderTop = "1px solid " + (darkMode ? "#374151" : "#e7ebf3");
              }
              if (groupKey) {
                var title = document.createElement("div");
                title.className = "diag-tooltip-group-title";
                title.textContent = groupKey;
                title.style.margin = "0 0 4px 0";
                title.style.fontSize = "0.63rem";
                title.style.textTransform = "uppercase";
                title.style.letterSpacing = "0.06em";
                title.style.fontWeight = "600";
                title.style.color = darkMode ? "#9ca3af" : "#6b7280";
                section.appendChild(title);
              }
              groups[groupKey].forEach(function(entry) {
                var row = document.createElement("div");
                row.className = "diag-tooltip-row";
                row.style.display = "flex";
                row.style.alignItems = "flex-start";
                row.style.gap = "6px";
                row.style.margin = "2px 0";
                var keyEl = document.createElement("span");
                keyEl.className = "diag-tooltip-key";
                keyEl.textContent = entry.key + ":";
                keyEl.style.display = "inline-block";
                keyEl.style.background = darkMode ? "#1f2937" : "#e9f1ff";
                keyEl.style.border = "1px solid " + (darkMode ? "#475569" : "#d3def3");
                keyEl.style.color = darkMode ? "#d1d5db" : "#334155";
                keyEl.style.borderRadius = "999px";
                keyEl.style.padding = "1px 7px";
                keyEl.style.fontSize = "0.66rem";
                keyEl.style.fontWeight = "600";
                keyEl.style.lineHeight = "1.3";
                keyEl.style.whiteSpace = "nowrap";
                var valueEl = document.createElement("span");
                valueEl.className = "diag-tooltip-value";
                valueEl.textContent = entry.value;
                valueEl.style.color = "inherit";
                valueEl.style.overflowWrap = "anywhere";
                valueEl.style.wordBreak = "break-word";
                row.appendChild(keyEl);
                row.appendChild(valueEl);
                section.appendChild(row);
              });
              root.appendChild(section);
            });

            this.eGui = root;
          };

          Tooltip.prototype.afterGuiAttached = function() {
            placeTooltip(this.params, this.eGui);
            var self = this;
            window.setTimeout(function() {
              placeTooltip(self.params, self.eGui);
            }, 20);
          };

          Tooltip.prototype.getGui = function() {
            return this.eGui;
          };

          return Tooltip;
        })()
        """
    )


def _build_aggrid_options(df: pd.DataFrame, edit_mode: bool) -> dict:
    gb = GridOptionsBuilder.from_dataframe(df)
    tooltip_component = _aggrid_diagnostics_tooltip_component()
    gb.configure_default_column(
        resizable=True,
        sortable=True,
        filter=False,
        editable=False,
    )
    gb.configure_grid_options(
        suppressRowClickSelection=False,
        rowSelection="multiple",
        rowMultiSelectWithClick=True,
        enableBrowserTooltips=False,
        tooltipMouseTrack=False,
        tooltipShowDelay=0,
        components={"diagnosticsTooltip": tooltip_component},
        getRowId=JsCode(
            f"""
            function(params) {{
              const row = (params && params.data) ? params.data : {{}};
              const gse = row.gse_accession || "";
              const gsm = row.gsm_accession || "";
              if (gse || gsm) {{
                return gse + "::" + gsm;
              }}
              const fallback = row.{AGGRID_ROW_INDEX_COLUMN};
              return (fallback === undefined || fallback === null) ? "" : String(fallback);
            }}
            """
        ),
        rowClassRules={
            "ag-row-has-flags": f"data.{AGGRID_ROW_HAS_FLAGS_COLUMN} === true"
        },
        onCellClicked=JsCode(
            f"""
            function(event) {{
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
        tooltipValueGetter=_aggrid_accession_tooltip_getter(),
        tooltipComponent="diagnosticsTooltip",
        pinned="left",
        lockPosition=True,
        lockPinned=True,
        suppressMovable=True,
        minWidth=130,
        width=140,
    )
    gb.configure_column(
        "gsm_accession",
        cellClass="ag-geo-link",
        tooltipValueGetter=_aggrid_accession_tooltip_getter(),
        tooltipComponent="diagnosticsTooltip",
        pinned="left",
        lockPosition=True,
        lockPinned=True,
        suppressMovable=True,
        minWidth=130,
        width=140,
    )

    for field in CANONICAL_FIELDS:
        override_rule = (
            f"data.__override_cell_{field} === true || "
            f"data.__override_cell_{field} === 'true' || "
            f"data.__override_cell_{field} === 'True' || "
            f"data.__override_cell_{field} === 1"
        )
        cell_rules = {"ag-cell-overridden": override_rule}
        flagged_rule = "false"
        if field in AGGRID_FLAG_FIELDS:
            flagged_rule = (
                f"data.__evidence_flagged_{field} === true || "
                f"data.__evidence_flagged_{field} === 'true' || "
                f"data.__evidence_flagged_{field} === 'True' || "
                f"data.__evidence_flagged_{field} === 1"
            )
            cell_rules["ag-cell-flagged"] = flagged_rule
            cell_rules["ag-cell-overridden-flagged"] = (
                f"({override_rule}) && ({flagged_rule})"
            )
        cell_style = JsCode(
            f"""
            function(params) {{
              const row = (params && params.data) ? params.data : {{}};
              const isOverridden =
                row.__override_cell_{field} === true ||
                row.__override_cell_{field} === 1 ||
                row.__override_cell_{field} === "true" ||
                row.__override_cell_{field} === "True";
              const isFlagged =
                row.__evidence_flagged_{field} === true ||
                row.__evidence_flagged_{field} === 1 ||
                row.__evidence_flagged_{field} === "true" ||
                row.__evidence_flagged_{field} === "True";
              if (isOverridden && isFlagged) {{
                return {{
                  backgroundColor: "#dff4df",
                  boxShadow: "inset 0 0 0 2px #e47b00"
                }};
              }}
              if (isOverridden) {{
                return {{ backgroundColor: "#dff4df" }};
              }}
              if (isFlagged) {{
                return {{ backgroundColor: "#ffe7cc" }};
              }}
              return {{}};
            }}
            """
        )
        gb.configure_column(
            field,
            editable=edit_mode,
            tooltipValueGetter=_aggrid_tooltip_getter(
                field, include_evidence=field in AGGRID_FLAG_FIELDS
            ),
            tooltipComponent="diagnosticsTooltip",
            cellClassRules=cell_rules,
            cellStyle=cell_style,
        )

    gb.configure_column(
        STATUS_COLUMN,
        header_name="",
        cellClass="ag-status-cell",
        cellClassRules={
            "ag-status-flagged": f"value === '🚩'",
            "ag-status-accept": f"value === '✅'",
        },
        pinned="left",
        lockPosition=True,
        lockPinned=True,
        suppressMovable=True,
        resizable=False,
        width=60,
    )
    gb.configure_column(
        CHECKED_COLUMN,
        header_name="",
        editable=True,
        singleClickEdit=True,
        cellRenderer="agCheckboxCellRenderer",
        cellEditor="agCheckboxCellEditor",
        pinned="left",
        lockPosition=True,
        lockPinned=True,
        suppressMovable=True,
        resizable=False,
        cellClass="ag-checked-cell",
        width=70,
    )
    gb.configure_column(
        EDITED_COLUMN,
        header_name="",
        editable=False,
        pinned="left",
        lockPosition=True,
        lockPinned=True,
        suppressMovable=True,
        resizable=False,
        cellClass="ag-edited-cell",
        width=60,
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
        EDITED_BOOL_COLUMN,
    ]
    hidden_columns.extend([f"evidence_flags_{field}" for field in AGGRID_FLAG_FIELDS])
    hidden_columns.extend(
        [f"__evidence_flagged_{field}" for field in AGGRID_FLAG_FIELDS]
    )
    hidden_columns.extend([f"__override_cell_{field}" for field in CANONICAL_FIELDS])
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


def _unsaved_override_change_keys(overrides: dict, saved_overrides: dict) -> set[tuple[str, str, str]]:
    keys: set[tuple[str, str, str]] = set()
    keys.update(overrides.keys())
    keys.update(saved_overrides.keys())
    unsaved: set[tuple[str, str, str]] = set()
    marker = object()
    for key in keys:
        if overrides.get(key, marker) != saved_overrides.get(key, marker):
            unsaved.add(key)
    return unsaved


def _render_unsaved_status_line(
    container: st.delta_generator.DeltaGenerator,
    overrides: dict,
    saved_overrides: dict,
) -> None:
    unsaved_changes = _unsaved_override_change_keys(overrides, saved_overrides)
    if not unsaved_changes:
        container.caption("No unsaved edits")
        return
    edited_gsms = {(gse, gsm) for gse, gsm, _ in unsaved_changes}
    container.caption(
        "Unsaved edits: "
        f"Edited GSMs: {len(edited_gsms)}; "
        f"Edited fields: {len(unsaved_changes)}"
    )


def _request_rerun() -> None:
    rerun = getattr(st, "rerun", None)
    if callable(rerun):
        rerun()
        return
    experimental_rerun = getattr(st, "experimental_rerun", None)
    if callable(experimental_rerun):
        experimental_rerun()


def _get_grid_version() -> int:
    version = st.session_state.get("grid_version", 0)
    if not isinstance(version, int):
        version = 0
    st.session_state["grid_version"] = version
    return version


def _bump_grid_version() -> int:
    version = _get_grid_version() + 1
    st.session_state["grid_version"] = version
    return version


def _table_df_equals(left: object, right: pd.DataFrame) -> bool:
    if not isinstance(left, pd.DataFrame):
        return False
    try:
        return left.equals(right)
    except Exception:
        return False


def _set_table_df(table_df: pd.DataFrame) -> bool:
    current = st.session_state.get("table_df")
    if _table_df_equals(current, table_df):
        return False
    st.session_state["table_df"] = table_df.copy()
    return True


def _table_df_changed_outside_columns(
    left: object,
    right: pd.DataFrame,
    ignored_columns: tuple[str, ...],
) -> bool:
    """Return True when a DataFrame changed in any non-ignored column."""
    if not isinstance(left, pd.DataFrame):
        return True
    if _table_df_equals(left, right):
        return False
    keep_left = left.drop(columns=list(ignored_columns), errors="ignore")
    keep_right = right.drop(columns=list(ignored_columns), errors="ignore")
    return not _table_df_equals(keep_left, keep_right)


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
        "Counts"
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


def _build_csv_content(
    header: tuple[str, ...],
    rows: list[dict[str, object]] | list[dict[str, str]],
) -> str:
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(list(header))
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
        "Biology"
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


def _render_gse_summary_section(
    gse_field_values: dict | None,
    has_session_edits: bool,
    *,
    total: int,
    flagged: int,
    overrides_saved: int,
    overrides_session: int,
    outliers: int,
) -> None:
    with st.expander("GSE-wide summary (not affected by filters)", expanded=False):
        st.caption("Not affected by filters.")
        _render_gse_field_values_summary(gse_field_values, has_session_edits)
        _render_gse_metrics(
            total=total,
            flagged=flagged,
            overrides_saved=overrides_saved,
            overrides_session=overrides_session,
            outliers=outliers,
        )


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


def _render_checked_bulk_controls(
    container: st.delta_generator.DeltaGenerator,
    gse_id: str,
) -> bool | None:
    controls = container.columns(2)
    check_all_visible = controls[0].button(
        "Check all",
        key=f"checked_visible_all_{gse_id}",
        use_container_width=True,
    )
    uncheck_all_visible = controls[1].button(
        "Uncheck all",
        key=f"checked_visible_none_{gse_id}",
        use_container_width=True,
    )
    if check_all_visible:
        return True
    if uncheck_all_visible:
        return False
    return None


def _build_editable_df(
    df_base: pd.DataFrame,
    overrides: dict,
    saved_overrides: dict,
    evidence_lookup: dict[tuple[str, str], dict],
    flags_by_gsm: dict[tuple[str, str], dict[str, list[str]]],
    flag_summaries: dict[tuple[str, str], dict[str, object]],
    primary_failures: dict[tuple[str, str], str],
    final_decisions: dict[tuple[str, str], str],
    review_counts: dict[tuple[str, str], int],
    terminal_fallback_counts: dict[tuple[str, str], int],
    outlier_categories_by_gsm: dict[tuple[str, str], list[str]],
    checked_state: dict[tuple[str, str], bool],
) -> pd.DataFrame:
    df_editable = df_base.copy()
    override_cell_columns: dict[str, list[bool]] = {
        field: [] for field in CANONICAL_FIELDS
    }
    for (gse, gsm, field), value in overrides.items():
        if field not in CANONICAL_FIELDS:
            continue
        mask = (df_editable["gse_accession"] == gse) & (
            df_editable["gsm_accession"] == gsm
        )
        if mask.any():
            df_editable.loc[mask, field] = format_override_value(value)

    for row in df_base.to_dict("records"):
        gse = row.get("gse_accession")
        gsm = row.get("gsm_accession")
        if not isinstance(gse, str) or not isinstance(gsm, str):
            for field in CANONICAL_FIELDS:
                override_cell_columns[field].append(False)
            continue
        for field in CANONICAL_FIELDS:
            override_cell_columns[field].append((gse, gsm, field) in overrides)

    edited_keys = {
        (gse, gsm) for gse, gsm, _ in overrides
    } | {
        (gse, gsm) for gse, gsm, _ in saved_overrides
    }
    is_edited_values = [
        (row["gse_accession"], row["gsm_accession"]) in edited_keys
        for row in df_base.to_dict("records")
    ]
    edited_values = [EDITED_ICON if value else "" for value in is_edited_values]
    status_values = [
        _decision_icon(
            final_decisions.get((row["gse_accession"], row["gsm_accession"]), "")
        )
        for row in df_base.to_dict("records")
    ]
    df_editable[STATUS_COLUMN] = status_values
    df_editable[EDITED_BOOL_COLUMN] = is_edited_values
    df_editable[EDITED_COLUMN] = edited_values

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

    checked_values = []
    for row in df_base.to_dict("records"):
        key = (row["gse_accession"], row["gsm_accession"])
        checked_values.append(bool(checked_state.get(key, False)))
    df_editable[CHECKED_COLUMN] = checked_values

    flagged_values = []
    for row in df_base.to_dict("records"):
        key = (row["gse_accession"], row["gsm_accession"])
        flagged = _evidence_flagged_fields(evidence_lookup, key)
        flagged_values.append(",".join(sorted(flagged)))
    df_editable["flagged_fields"] = flagged_values
    for field, values in override_cell_columns.items():
        df_editable[f"__override_cell_{field}"] = values
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


def _bulk_selection_state_key(gse_id: str) -> str:
    return f"bulk_selected_rows_{gse_id}"


def _bulk_selection_signature_key(gse_id: str) -> str:
    return f"bulk_selection_signature_{gse_id}"


def _bulk_field_state_key(gse_id: str) -> str:
    return f"bulk_edit_field_{gse_id}"


def _bulk_value_state_key(gse_id: str) -> str:
    return f"bulk_edit_value_{gse_id}"


def _bulk_mode_state_key(gse_id: str) -> str:
    return f"bulk_edit_mode_{gse_id}"


def _bulk_mode_reset_pending_key(gse_id: str) -> str:
    return f"bulk_edit_mode_reset_pending_{gse_id}"


def _reset_bulk_edit_mode_state(gse_id: str) -> None:
    field_key = _bulk_field_state_key(gse_id)
    value_key = _bulk_value_state_key(gse_id)
    mode_key = _bulk_mode_state_key(gse_id)
    reset_bulk_mode_state(
        st.session_state,
        mode_key=mode_key,
        field_key=field_key,
        value_key=value_key,
    )


def _bulk_target_column_label(value: str) -> str:
    if not value:
        return "Select column"
    return value


def _bulk_preview_value(value: object) -> str:
    if isinstance(value, str) and not value.strip():
        return "(empty)"
    if isinstance(value, list) and not value:
        return "(empty)"
    displayed = _format_override_display(value)
    if not displayed:
        return "(empty)"
    return displayed


def _bulk_missing_requirements(
    edit_mode: bool,
    target_field: str,
    selected_count: int,
    new_value: object,
) -> list[str]:
    missing: list[str] = []
    if not target_field:
        missing.append("target column")
    if selected_count <= 0:
        missing.append("row selection")
    if is_empty_bulk_value(new_value):
        missing.append("new value")
    if not edit_mode:
        missing.append("edit mode")
    return missing


def _render_bulk_preview_card(
    target_field: str,
    selected_count: int,
    changed_count: int,
    no_op_count: int,
    new_value: object,
) -> None:
    preview_items = [
        ("Selected rows", str(selected_count)),
        ("Target column", target_field),
        ("New value", _bulk_preview_value(new_value)),
        ("Will change", str(changed_count)),
        ("No-op rows", str(no_op_count)),
    ]
    blocks = []
    for label, value in preview_items:
        blocks.append(
            "<div class=\"bulk-preview-item\">"
            f"<div class=\"label\">{html.escape(label)}</div>"
            f"<div class=\"value\">{html.escape(value)}</div>"
            "</div>"
        )
    html_block = (
        "<div class=\"bulk-preview-card\">"
        "<div class=\"bulk-preview-title\">Bulk edit preview</div>"
        "<div class=\"bulk-preview-grid\">"
        + "".join(blocks)
        + "</div></div>"
    )
    st.markdown(html_block, unsafe_allow_html=True)


def _render_bulk_edit_panel(
    gse_id: str,
    filtered_rows: list[dict[str, object]],
    selected_rows: list[int],
    overrides: dict,
    evidence_lookup: dict[tuple[str, str], dict],
    edit_mode: bool,
) -> tuple[dict, bool, bool]:
    pending_reset_key = _bulk_mode_reset_pending_key(gse_id)
    if bool(st.session_state.pop(pending_reset_key, False)):
        _reset_bulk_edit_mode_state(gse_id)

    mode_key = _bulk_mode_state_key(gse_id)
    mode_active = is_bulk_mode_active(st.session_state, mode_key)
    if not mode_active:
        open_mode_clicked = st.button(
            "Bulk edit",
            key=f"bulk_mode_open_{gse_id}",
            help=bulk_edit_tooltip(),
        )
        if not open_mode_clicked:
            return overrides, False, False
        activate_bulk_mode(st.session_state, mode_key)

    field_key = _bulk_field_state_key(gse_id)
    value_key = _bulk_value_state_key(gse_id)
    field_options = ["", *CANONICAL_FIELDS]
    current_field = st.session_state.get(field_key, "")
    if current_field not in field_options:
        st.session_state[field_key] = ""

    header_cols = st.columns([4, 1])
    header_cols[0].caption("Bulk edit mode")
    close_mode_clicked = header_cols[1].button(
        "Close",
        key=f"bulk_mode_close_{gse_id}",
    )
    if close_mode_clicked:
        _reset_bulk_edit_mode_state(gse_id)
        _request_rerun()
        return overrides, False, False

    panel_cols = st.columns([2, 3, 2])
    target_field = panel_cols[0].selectbox(
        "Target column",
        field_options,
        key=field_key,
        format_func=_bulk_target_column_label,
    )
    panel_cols[1].text_input(
        "New value",
        key=value_key,
        placeholder="Enter a value to apply",
    )
    new_value = parse_override_input(st.session_state.get(value_key, ""))
    selected_keys = resolve_selected_keys(filtered_rows, selected_rows)

    use_selected_value_clicked = panel_cols[2].button(
        "Use value from first selected row",
        key=f"bulk_fill_value_{gse_id}",
        disabled=(not target_field or not selected_keys),
    )
    if use_selected_value_clicked and target_field and selected_keys:
        first_key = selected_keys[0]
        row_lookup = {
            (row["gse_accession"], row["gsm_accession"]): row for row in filtered_rows
        }
        row = row_lookup.get(first_key, {})
        current_value = overrides.get(
            (first_key[0], first_key[1], target_field),
            row.get(target_field, ""),
        )
        st.session_state[value_key] = _format_override_input(current_value)
        _request_rerun()
        return overrides, False, False

    preview = build_bulk_edit_preview(
        filtered_rows,
        selected_rows,
        target_field,
        new_value,
        overrides,
    )
    if target_field:
        _render_bulk_preview_card(
            target_field=target_field,
            selected_count=preview["selected_count"],
            changed_count=preview["changed_count"],
            no_op_count=preview["no_op_count"],
            new_value=new_value,
        )
        sample_rows = build_bulk_edit_samples(
            filtered_rows,
            selected_rows,
            target_field,
            new_value,
            overrides,
            limit=BULK_EDIT_SAMPLE_LIMIT,
        )
        if sample_rows:
            sample_records = []
            for sample in sample_rows:
                sample_records.append(
                    {
                        "gsm_accession": sample["gsm_accession"],
                        "old value": _bulk_preview_value(sample["current_value"]),
                        "new value": _bulk_preview_value(sample["new_value"]),
                        "result": (
                            "No-op (already matches)"
                            if sample["is_no_op"]
                            else "Will change"
                        ),
                    }
                )
            st.caption(
                "Sample selection preview "
                f"({len(sample_records)} of {preview['selected_count']} selected)"
            )
            st.dataframe(
                pd.DataFrame(sample_records),
                hide_index=True,
                use_container_width=True,
            )

    missing_requirements = _bulk_missing_requirements(
        edit_mode=edit_mode,
        target_field=target_field,
        selected_count=preview["selected_count"],
        new_value=new_value,
    )
    ready_to_apply = len(missing_requirements) == 0
    if ready_to_apply:
        st.success("Ready to apply bulk edit.")
    else:
        st.warning("Missing: " + ", ".join(missing_requirements))

    apply_clicked = st.button(
        f"Apply to selected ({preview['selected_count']})",
        key=f"bulk_apply_{gse_id}",
        disabled=not ready_to_apply,
    )

    if not apply_clicked:
        return overrides, False, False

    failures = validate_bulk_edit(
        filtered_rows,
        selected_rows,
        target_field,
        evidence_lookup,
        edit_mode=edit_mode,
    )
    if failures:
        st.error(
            "Bulk edit blocked: some selected rows failed override safety checks. "
            "No changes were applied."
        )
        st.dataframe(pd.DataFrame(failures), hide_index=True, use_container_width=True)
        return overrides, False, False

    updated_overrides, changed_count, no_op_count = apply_bulk_edit(
        filtered_rows,
        selected_rows,
        target_field,
        new_value,
        overrides,
    )
    if changed_count:
        st.success(
            f"Bulk edit applied to {changed_count} row(s). "
            f"No-op rows: {no_op_count}."
        )
    else:
        st.info("Bulk edit produced no changes for selected rows.")
    return updated_overrides, updated_overrides != overrides, True


def _overrides_path(active_paths: InputPaths) -> Path:
    return active_paths.input_dir / "overrides.jsonl"


def _checked_path(active_paths: InputPaths) -> Path:
    return active_paths.input_dir / "checked.jsonl"


def _load_checked_jsonl(path: Path, gse_accession: str) -> dict[tuple[str, str], bool]:
    if not path.exists():
        return {}
    checked: dict[tuple[str, str], bool] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                record = json.loads(stripped)
            except json.JSONDecodeError:
                continue
            if not isinstance(record, dict):
                continue
            gse = record.get("gse_accession")
            gsm = record.get("gsm_accession")
            if not isinstance(gse, str) or not isinstance(gsm, str):
                continue
            if gse != gse_accession:
                continue
            checked_value = record.get("checked")
            if not isinstance(checked_value, bool):
                continue
            checked[(gse, gsm)] = checked_value
    return checked


def _ensure_checked_state(
    gse_accession: str,
    active_paths: InputPaths,
) -> tuple[dict, bool]:
    checked_by_gse = st.session_state.get("checked_by_gse", {})
    if not isinstance(checked_by_gse, dict):
        checked_by_gse = {}

    path = _checked_path(active_paths)
    checked_present = path.is_file()
    if gse_accession not in checked_by_gse:
        if checked_present:
            checked_by_gse[gse_accession] = _load_checked_jsonl(
                path, gse_accession
            )
        else:
            checked_by_gse[gse_accession] = {}
    else:
        existing = checked_by_gse.get(gse_accession, {})
        checked_by_gse[gse_accession] = (
            dict(existing) if isinstance(existing, dict) else {}
        )

    st.session_state["checked_by_gse"] = checked_by_gse
    return checked_by_gse, checked_present


def _normalize_checked_value(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "yes", "1"}:
            return True
        if normalized in {"false", "no", "0", ""}:
            return False
    return False


def _extract_checked_updates(df: pd.DataFrame) -> dict[tuple[str, str], bool]:
    updates: dict[tuple[str, str], bool] = {}
    for row in df.to_dict("records"):
        gse = row.get("gse_accession")
        gsm = row.get("gsm_accession")
        if not isinstance(gse, str) or not isinstance(gsm, str):
            continue
        updates[(gse, gsm)] = _normalize_checked_value(row.get(CHECKED_COLUMN))
    return updates


def _merge_checked(
    existing: dict[tuple[str, str], bool],
    updates: dict[tuple[str, str], bool],
    visible_keys: set[tuple[str, str]],
) -> dict[tuple[str, str], bool]:
    merged = {
        key: value for key, value in existing.items() if key not in visible_keys
    }
    merged.update(updates)
    return merged


def _persist_checked_updates(
    active_paths: InputPaths,
    gse_accession: str,
    updates: dict[tuple[str, str], bool],
) -> None:
    if not updates:
        return
    path = _checked_path(active_paths)
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    lines: list[str] = []
    for (gse, gsm), checked in updates.items():
        if gse != gse_accession:
            continue
        record = {
            "gse_accession": gse,
            "gsm_accession": gsm,
            "checked": checked,
            "updated_at": timestamp,
        }
        lines.append(json.dumps(record))
    if not lines:
        return
    with path.open("a", encoding="utf-8") as handle:
        for line in lines:
            handle.write(line + "\n")


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


def _render_overrides_persistence_status(
    overrides: dict,
    saved_overrides: dict,
    saved_present: bool,
) -> None:
    edited_gsms = {(gse, gsm) for gse, gsm, _ in overrides}
    st.caption(f"Edited GSMs: {len(edited_gsms)} | Edited fields: {len(overrides)}")
    with st.expander("Overrides (persistent)", expanded=False):
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


def _apply_overrides_persistence_actions(
    active_paths: InputPaths,
    gse_accession: str,
    overrides: dict,
    saved_overrides: dict,
    saved_present: bool,
    save_clicked: bool,
    revert_clicked: bool,
    discard_clicked: bool,
    discard_confirm: bool,
) -> tuple[dict, dict, bool]:
    if save_clicked:
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
            st.session_state.pop("all_export_cache", None)
        else:
            st.info("No overrides to save.")

    if revert_clicked:
        overrides = dict(saved_overrides)
        st.info("Reverted to saved overrides.")

    if discard_clicked:
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
                st.session_state.pop("all_export_cache", None)
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
    return overrides, saved_overrides, saved_present


def _collect_summarize_exports(
    inputs: InputScanResult,
) -> tuple[str, str, int, int, list[str], list[str], list[str]]:
    skipped = [f"{name}: {reason}" for name, reason in sorted(inputs.skipped.items())]
    override_errors: list[str] = []
    summary_warnings: list[str] = []
    gsm_rows: list[dict[str, object]] = []
    ignore_values_by_gse: dict[str, list[str]] = {}

    for gse_name, paths in summarize_cli._iter_scan_paths(inputs):
        try:
            curation_records = load_curation_jsonl(str(paths.curation_path))
            gse_accession = summarize_cli._resolve_gse_accession(curation_records, gse_name)
            try:
                ignore_values_by_gse[gse_accession] = summarize_cli._load_ignore_values(paths)
            except Exception as exc:
                ignore_values_by_gse[gse_accession] = list(summarize_cli._DEFAULT_IGNORE_VALUES)
                summary_warnings.append(
                    f"{gse_accession}: invalid gse_field_values.jsonl; default ignore values used ({exc})"
                )

            overrides: dict = {}
            auto_path = paths.input_dir / "overrides.jsonl"
            if auto_path.is_file():
                try:
                    overrides = load_overrides_jsonl(str(auto_path), gse_accession)
                except Exception as exc:
                    override_errors.append(f"{gse_accession}: {exc}")
                    overrides = {}

            gsm_rows.extend(summarize_cli._build_gsm_rows(curation_records, overrides))
        except Exception as exc:
            skipped.append(f"{gse_name}: {exc}")

    gsm_rows.sort(
        key=lambda row: (
            str(row.get("gse_accession", "")),
            str(row.get("gsm_accession", "")),
        )
    )
    gse_rows = summarize_cli._build_gse_rows(gsm_rows, ignore_values_by_gse)
    gsm_csv_content = _build_csv_content(summarize_cli._GSM_CSV_COLUMNS, gsm_rows)
    gse_csv_content = _build_csv_content(summarize_cli._GSE_CSV_COLUMNS, gse_rows)
    return (
        gsm_csv_content,
        gse_csv_content,
        len(gsm_rows),
        len(gse_rows),
        skipped,
        override_errors,
        summary_warnings,
    )


def _all_export_signature(inputs: InputScanResult) -> tuple[object, ...]:
    entries: list[object] = [str(inputs.input_dir)]
    for gse_name, paths in summarize_cli._iter_scan_paths(inputs):
        try:
            curation_mtime = paths.curation_path.stat().st_mtime_ns
        except OSError:
            curation_mtime = None
        overrides_path = _overrides_path(paths)
        try:
            overrides_mtime = (
                overrides_path.stat().st_mtime_ns
                if overrides_path.exists()
                else None
            )
        except OSError:
            overrides_mtime = None
        try:
            gse_values_mtime = (
                paths.gse_field_values_path.stat().st_mtime_ns
                if paths.gse_field_values_path.exists()
                else None
            )
        except OSError:
            gse_values_mtime = None
        entries.append((gse_name, curation_mtime, overrides_mtime, gse_values_mtime))
    return tuple(entries)


def _load_summarize_export_cache(inputs: InputScanResult) -> dict[str, object]:
    signature = _all_export_signature(inputs)
    cache = st.session_state.get("all_export_cache")
    if isinstance(cache, dict) and cache.get("signature") == signature:
        return cache
    try:
        (
            gsm_csv_content,
            gse_csv_content,
            gsm_row_count,
            gse_row_count,
            skipped,
            override_errors,
            summary_warnings,
        ) = _collect_summarize_exports(inputs)
        cache = {
            "signature": signature,
            "gsm_csv": gsm_csv_content,
            "gse_csv": gse_csv_content,
            "gsm_row_count": gsm_row_count,
            "gse_row_count": gse_row_count,
            "skipped": skipped,
            "override_errors": override_errors,
            "summary_warnings": summary_warnings,
            "error": "",
        }
    except Exception as exc:
        cache = {
            "signature": signature,
            "gsm_csv": "",
            "gse_csv": "",
            "gsm_row_count": 0,
            "gse_row_count": 0,
            "skipped": [],
            "override_errors": [],
            "summary_warnings": [],
            "error": str(exc),
        }
    st.session_state["all_export_cache"] = cache
    return cache


def _render_summarize_export_notices(
    skipped: list[str],
    override_errors: list[str],
    summary_warnings: list[str],
    *,
    sidebar: bool,
) -> None:
    target = st.sidebar if sidebar else st
    if skipped:
        target.warning("Skipped GSEs during summarize export: " + "; ".join(skipped))
    if override_errors:
        target.warning("Overrides not applied for: " + "; ".join(override_errors))
    if summary_warnings:
        target.warning("; ".join(summary_warnings))


def _render_summarize_export_buttons(
    *,
    gsm_csv_content: str,
    gse_csv_content: str,
    gsm_row_count: int,
    gse_row_count: int,
    input_dir_name: str,
    sidebar: bool,
) -> None:
    if sidebar:
        left, right = st.sidebar.columns(2)
        left.download_button(
            "GSMs",
            data=gsm_csv_content,
            file_name=f"{input_dir_name}_gsm_annotations.csv",
            mime="text/csv",
            disabled=gsm_row_count == 0,
            help="Export GSM-level CSV (8 canonical fields)",
        )
        right.download_button(
            "GSEs",
            data=gse_csv_content,
            file_name=f"{input_dir_name}_gse_summary.csv",
            mime="text/csv",
            disabled=gse_row_count == 0,
            help="Export GSE-level CSV (7 fields, summarize output)",
        )
        return

    export_cols = st.columns(2)
    export_cols[0].download_button(
        "GSMs",
        data=gsm_csv_content,
        file_name=f"{input_dir_name}_gsm_annotations.csv",
        mime="text/csv",
        disabled=gsm_row_count == 0,
        help="Export GSM-level CSV (8 canonical fields)",
    )
    export_cols[1].download_button(
        "GSEs",
        data=gse_csv_content,
        file_name=f"{input_dir_name}_gse_summary.csv",
        mime="text/csv",
        disabled=gse_row_count == 0,
        help="Export GSE-level CSV (7 fields, summarize output)",
    )


def _render_export_final_annotations(inputs: InputScanResult) -> None:
    cache = _load_summarize_export_cache(inputs)
    error = cache.get("error", "")
    with st.expander("Exports", expanded=False):
        if error:
            st.error(
                "Export generation failed for geo-gsm-summarize-equivalent outputs: "
                f"{error}"
            )
            return
        _render_summarize_export_notices(
            cache.get("skipped", []),
            cache.get("override_errors", []),
            cache.get("summary_warnings", []),
            sidebar=False,
        )
        _render_summarize_export_buttons(
            gsm_csv_content=str(cache.get("gsm_csv", "")),
            gse_csv_content=str(cache.get("gse_csv", "")),
            gsm_row_count=int(cache.get("gsm_row_count", 0)),
            gse_row_count=int(cache.get("gse_row_count", 0)),
            input_dir_name=inputs.input_dir.name,
            sidebar=False,
        )


def _render_export_all_sidebar(inputs: InputScanResult) -> None:
    st.sidebar.header("Exports")
    cache = _load_summarize_export_cache(inputs)
    error = cache.get("error", "")
    if error:
        st.sidebar.error(
            "Export generation failed for geo-gsm-summarize-equivalent outputs: "
            f"{error}"
        )
        return
    _render_summarize_export_notices(
        cache.get("skipped", []),
        cache.get("override_errors", []),
        cache.get("summary_warnings", []),
        sidebar=True,
    )
    _render_summarize_export_buttons(
        gsm_csv_content=str(cache.get("gsm_csv", "")),
        gse_csv_content=str(cache.get("gse_csv", "")),
        gsm_row_count=int(cache.get("gsm_row_count", 0)),
        gse_row_count=int(cache.get("gse_row_count", 0)),
        input_dir_name=inputs.input_dir.name,
        sidebar=True,
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
        _render_export_all_sidebar(inputs)
        active_paths = inputs.gse_paths[active_gse]
    else:
        active_gse = None
        active_paths = inputs.single_paths if inputs.single_paths else None
        if active_paths is None:
            st.error("No valid input directory found.")
            st.stop()
        _render_export_all_sidebar(inputs)

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

    _render_header(active_gse=active_gse)
    if inputs.mode == "multi":
        _render_skipped_panel(inputs.skipped)

    rows = build_table_rows(curation_records)
    gse_filter, search_text = _render_filters(rows)
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
    checked_by_gse, checked_present = _ensure_checked_state(gse_id, active_paths)
    overrides = overrides_by_gse.get(gse_id, {})
    saved_overrides = saved_by_gse.get(gse_id, {})
    raw_checked_state = checked_by_gse.get(gse_id, {})
    checked_state = dict(raw_checked_state) if isinstance(raw_checked_state, dict) else {}
    active_row_idx = st.session_state.get("active_row_idx")
    if not isinstance(active_row_idx, int):
        active_row_idx = None
    grid_version = _get_grid_version()
    grid_version_bumped = False

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
    _render_gse_summary_section(
        gse_field_values,
        has_biology_edits,
        total=len(rows),
        flagged=flagged_count,
        overrides_saved=len(saved_override_keys),
        overrides_session=len(session_override_keys),
        outliers=outlier_count,
    )
    _section_divider()
    header_cols = st.columns([3, 5])
    table_header_placeholder = header_cols[0].empty()
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
    debug_table = _render_table_debug_toggle()
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
    table_header_placeholder.markdown(
        "### Curation table "
        f"<span style=\"display:inline-block; margin-left:0.45rem; "
        "padding:0.08rem 0.5rem; border-radius:999px; "
        "background:#f2f4f7; border:1px solid #d7dde7; "
        "font-size:0.72rem; font-weight:600; color:#4b5563; "
        "vertical-align:middle;\">"
        f"Rows: {len(filtered_rows)}</span> "
        f"{_help_icon_html(table_legend_tooltip())} "
        f"{_help_icon_html(table_guidance_text())}",
        unsafe_allow_html=True,
    )

    if not filtered_rows:
        st.info("No records match the current filters.")
        st.stop()

    checked_bulk_action = _render_checked_bulk_controls(header_cols[0], gse_id)
    header_cols[0].caption("Checked actions apply to visible rows only.")
    if checked_bulk_action is not None:
        merged_checked, checked_changes = merge_visible_checked_updates(
            checked_state,
            filtered_rows,
            checked_bulk_action,
        )
        if checked_changes:
            _persist_checked_updates(active_paths, gse_id, checked_changes)
            checked_state = dict(merged_checked)
            checked_by_gse = dict(checked_by_gse)
            checked_by_gse[gse_id] = checked_state
            st.session_state["checked_by_gse"] = checked_by_gse
            if not grid_version_bumped:
                grid_version = _bump_grid_version()
                grid_version_bumped = True

    selected_rows_key = _bulk_selection_state_key(gse_id)
    selected_signature_key = _bulk_selection_signature_key(gse_id)
    current_selection_signature = tuple(
        (row["gse_accession"], row["gsm_accession"]) for row in filtered_rows
    )
    previous_selection_signature = st.session_state.get(selected_signature_key)
    if previous_selection_signature == current_selection_signature:
        selected_rows = normalize_selected_rows(
            st.session_state.get(selected_rows_key, []),
            len(filtered_rows),
        )
    else:
        selected_rows = []
    st.session_state[selected_signature_key] = current_selection_signature
    st.session_state[selected_rows_key] = selected_rows
    overrides, bulk_edit_changed, bulk_edit_apply_succeeded = _render_bulk_edit_panel(
        gse_id,
        filtered_rows,
        selected_rows,
        overrides,
        evidence_lookup,
        edit_mode=True,
    )
    if bulk_edit_changed:
        overrides_by_gse[gse_id] = overrides
        st.session_state["overrides_by_gse"] = overrides_by_gse
        if not grid_version_bumped:
            grid_version = _bump_grid_version()
            grid_version_bumped = True
    if bulk_edit_apply_succeeded:
        st.session_state[_bulk_mode_reset_pending_key(gse_id)] = True
        _request_rerun()

    active_selection = resolve_selected_key(filtered_rows, selected_rows[:1])
    if active_selection is None and isinstance(active_row_idx, int):
        active_selection = resolve_selected_key(filtered_rows, [active_row_idx])
    revert_row_clicked = False
    clear_all_clicked = False

    persist_cols = st.columns([1, 3])
    save_overrides_clicked = persist_cols[0].button("Save overrides")
    unsaved_status_container = persist_cols[0].empty()
    revert_saved_clicked = False
    discard_saved_clicked = False
    discard_confirm = False
    with persist_cols[1].expander("More actions"):
        st.caption("Session edit actions")
        revert_row_clicked = st.button(
            "Revert selected row",
            disabled=active_selection is None,
        )
        clear_all_clicked = st.button("Clear all edits")
        st.markdown("---")
        st.caption("Saved override actions")
        revert_saved_clicked = st.button("Revert to saved")
        discard_confirm = st.checkbox(
            "Confirm discard saved overrides",
            key=f"confirm_discard_overrides_{gse_id}",
        )
        discard_saved_clicked = st.button("Discard saved overrides")

    if revert_row_clicked:
        overrides = clear_overrides_for_gsm(
            overrides, active_selection[0], active_selection[1]
        )
        overrides_by_gse[gse_id] = overrides
        st.session_state["overrides_by_gse"] = overrides_by_gse
    if clear_all_clicked:
        overrides = clear_all_overrides(overrides)
        overrides_by_gse[gse_id] = overrides
        st.session_state["overrides_by_gse"] = overrides_by_gse
    if revert_row_clicked or clear_all_clicked:
        grid_version = _bump_grid_version()
        grid_version_bumped = True

    overrides_snapshot = dict(overrides)

    df_base = pd.DataFrame(filtered_rows)
    table_df = _build_editable_df(
        df_base,
        overrides,
        saved_overrides,
        evidence_lookup,
        flags_by_gsm,
        flag_summaries,
        primary_failures,
        final_decisions,
        review_counts,
        terminal_fallback_counts,
        outlier_categories_by_gsm,
        checked_state,
    )
    table_df = _append_aggrid_meta_columns(
        table_df,
        curation_lookup,
        evidence_lookup,
        audit_lookup,
        flag_summaries,
        primary_failures,
    )
    previous_table_df = st.session_state.get("table_df")
    table_df_changed = _set_table_df(table_df)
    table_df_requires_remount = _table_df_changed_outside_columns(
        previous_table_df,
        table_df,
        (CHECKED_COLUMN,),
    )
    if table_df_changed and table_df_requires_remount and not grid_version_bumped:
        grid_version = _bump_grid_version()
        grid_version_bumped = True
    table_df_state = st.session_state.get("table_df")
    if isinstance(table_df_state, pd.DataFrame):
        table_df = table_df_state
    _render_table_debug(debug_table, grid_version, table_df)
    grid_response = _render_aggrid_table(
        table_df,
        edit_mode=True,
        key=f"curation_grid_{grid_version}",
    )
    selected_rows = normalize_selected_rows(
        _extract_aggrid_selected_rows(grid_response, table_df),
        len(filtered_rows),
    )
    st.session_state[selected_signature_key] = current_selection_signature
    st.session_state[selected_rows_key] = selected_rows
    df_edited = _extract_aggrid_data(grid_response, table_df)
    overrides_visible = compute_overrides(df_base, df_edited)
    visible_keys = {
        (row["gse_accession"], row["gsm_accession"]) for row in filtered_rows
    }
    overrides = _merge_overrides(overrides, overrides_visible, visible_keys)
    overrides_changed = overrides != overrides_snapshot
    overrides_by_gse[gse_id] = overrides
    st.session_state["overrides_by_gse"] = overrides_by_gse
    checked_updates = _extract_checked_updates(df_edited)
    merged_checked = _merge_checked(checked_state, checked_updates, visible_keys)
    checked_changes = {
        key: value
        for key, value in merged_checked.items()
        if checked_state.get(key) != value
    }
    if checked_changes:
        _persist_checked_updates(active_paths, gse_id, checked_changes)
        checked_state = dict(merged_checked)
        checked_by_gse = dict(checked_by_gse)
        checked_by_gse[gse_id] = checked_state
        st.session_state["checked_by_gse"] = checked_by_gse

    if selected_rows:
        row_idx = selected_rows[0]
        st.session_state["active_row_idx"] = row_idx
        active_row_idx = row_idx

    overrides_before_persistence = dict(overrides)
    saved_overrides_snapshot = dict(saved_overrides)
    saved_present_snapshot = saved_present
    overrides, saved_overrides, saved_present = _apply_overrides_persistence_actions(
        active_paths,
        gse_id,
        overrides,
        saved_overrides,
        saved_present,
        save_overrides_clicked,
        revert_saved_clicked,
        discard_saved_clicked,
        discard_confirm,
    )
    _render_unsaved_status_line(unsaved_status_container, overrides, saved_overrides)
    persistence_changed = (
        overrides != overrides_before_persistence
        or saved_overrides != saved_overrides_snapshot
        or saved_present != saved_present_snapshot
    )
    rerun_needed = (
        overrides_changed
        or (persistence_changed and (revert_saved_clicked or discard_saved_clicked))
    )
    if rerun_needed:
        refreshed_table_df = _build_editable_df(
            df_base,
            overrides,
            saved_overrides,
            evidence_lookup,
            flags_by_gsm,
            flag_summaries,
            primary_failures,
            final_decisions,
            review_counts,
            terminal_fallback_counts,
            outlier_categories_by_gsm,
            checked_state,
        )
        refreshed_table_df = _append_aggrid_meta_columns(
            refreshed_table_df,
            curation_lookup,
            evidence_lookup,
            audit_lookup,
            flag_summaries,
            primary_failures,
        )
        _set_table_df(refreshed_table_df)
        _bump_grid_version()
        _request_rerun()




run_app()
