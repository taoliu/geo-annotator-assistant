"""Streamlit UI for reviewing curation artifacts."""

from __future__ import annotations

import argparse
import html
import inspect
import os
from collections import Counter
from pathlib import Path

import pandas as pd
import streamlit as st

from ui.flags import (
    FLAG_CATEGORY_BADGES,
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
    table_guidance_text,
    table_help_lines,
)
from ui.dashboard import BADGE_TOOLTIPS, build_dashboard_items
from ui.evidence import EVIDENCE_FIELDS, extract_field_evidence
from ui.loaders import (
    load_audit_jsonl_optional,
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
from ui.styling import style_curation_table
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
    list[dict],
    str | None,
]:
    paths = resolve_input_paths(input_dir)
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
    return (
        paths,
        curation_records,
        evidence_records,
        suggestions_records,
        audit_records,
        audit_error,
    )


def _render_header(paths: InputPaths) -> None:
    st.title("GEO GSM Curator UI")
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

    st.caption(f"Most common primary failures: {_top_items(primary_counts)}")
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
    _render_field_status_dashboard(details)
    _render_field_override_controls(details, edit_mode)
    _render_field_evidence_panels(details)
    evidence = details["evidence"]
    suggestions = details["suggestions"]
    flagged_fields = details["flagged_fields"]
    curation = details["curation"]
    curation_raw = curation["raw"] if curation else None
    curation_flags = extract_curation_flags(curation_raw)
    primary_failure = extract_primary_failure(curation_raw)
    flag_groups = build_flag_display_groups(curation_flags, flagged_fields)

    st.caption(f"Evidence present: {'yes' if evidence else 'no'}")
    if suggestions_present:
        st.caption(f"Suggestions: {len(suggestions)}")
    else:
        st.caption("Suggestions: 0 (not loaded)")

    st.markdown("**Flags**")
    st.caption("Grouped for visual scanning only; no backend changes.")
    has_secondary = any(flag_groups.get(category) for category in FLAG_CATEGORY_ORDER)
    if not primary_failure and not has_secondary:
        st.write("None.")
    else:
        if primary_failure:
            _render_primary_failure(primary_failure)
        for category in FLAG_CATEGORY_ORDER:
            _render_flag_group(category, flag_groups.get(category, []))

    _render_override_diff(details, curation_flags, flag_groups)

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


def _render_summary_strip(
    rows: list[TableRow],
    triage_flags: dict[tuple[str, str], dict[str, bool]],
) -> None:
    total = len(rows)
    needs_attention = sum(
        1 for flags in triage_flags.values() if flags.get("needs_attention")
    )
    has_overrides = sum(
        1 for flags in triage_flags.values() if flags.get("has_overrides")
    )
    clean = sum(1 for flags in triage_flags.values() if flags.get("is_clean"))

    cols = st.columns(4)
    cols[0].markdown(f"**Total GSMs**\n{total}")
    cols[1].markdown(f"**Needs attention**\n{needs_attention}")
    cols[2].markdown(f"**Has overrides**\n{has_overrides}")
    cols[3].markdown(f"**Clean**\n{clean}")
    st.caption("Summary reflects current GSE/search filters.")


def _render_triage_filters() -> str:
    st.markdown("**Quick filter (single choice)**")
    return st.radio(
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
    flags_by_gsm: dict[tuple[str, str], dict[str, list[str]]],
    triage_flags: dict[tuple[str, str], dict[str, bool]],
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
    df_editable.insert(2, "Decision", [
        final_decisions.get((row["gse_accession"], row["gsm_accession"]), "")
        for row in df_base.to_dict("records")
    ])
    df_editable.insert(3, "Edited", edited_values)

    attention_values = []
    for row in df_base.to_dict("records"):
        key = (row["gse_accession"], row["gsm_accession"])
        flags = triage_flags.get(key, {})
        attention_values.append("ATTN" if flags.get("needs_attention") else "")
    df_editable.insert(4, "Needs attention", attention_values)

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
    df_editable.insert(5, "Review flags", review_values)
    df_editable.insert(6, "Terminal fallbacks", terminal_values)
    df_editable.insert(7, "Outliers", outlier_values)
    df_editable.insert(8, "Primary failure", primary_values)
    df_editable.insert(9, "Flag summary", summary_values)

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
        (
            paths,
            curation_records,
            evidence_records,
            suggestions_records,
            audit_records,
            audit_error,
        ) = _load_records(input_dir)
    except Exception as exc:
        st.error(str(exc))
        st.stop()

    if audit_error:
        st.warning(
            "audit.jsonl could not be loaded; continuing without LLM originals. "
            f"Details: {audit_error}"
        )

    _render_header(paths)

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

    triage_flags = build_triage_flags(base_rows, evidence_lookup, overrides)
    _render_summary_strip(base_rows, triage_flags)
    _render_gse_summary_panel(
        base_rows,
        final_decisions,
        primary_failures,
        combined_flags_by_gsm,
        overrides,
        outlier_categories_by_gsm,
    )
    triage_filter = _render_triage_filters()
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
        df_editable = _build_editable_df(
            df_base,
            overrides,
            flags_by_gsm,
            triage_flags,
            flag_summaries,
            primary_failures,
            final_decisions,
            review_counts,
            terminal_fallback_counts,
            outlier_categories_by_gsm,
        )
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
            decision_values = [
                final_decisions.get((row["gse_accession"], row["gsm_accession"]), "")
                for row in filtered_rows
            ]
            df.insert(2, "Decision", decision_values)
            df.insert(3, "Edited", edited_values)
            attention_values = []
            for row in filtered_rows:
                key = (row["gse_accession"], row["gsm_accession"])
                flags = triage_flags.get(key, {})
                attention_values.append("ATTN" if flags.get("needs_attention") else "")
            df.insert(4, "Needs attention", attention_values)
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
            df.insert(5, "Review flags", review_values)
            df.insert(6, "Terminal fallbacks", terminal_values)
            df.insert(7, "Outliers", outlier_values)
            df.insert(8, "Primary failure", primary_values)
            df.insert(9, "Flag summary", summary_values)
        styled = style_curation_table(
            df,
            flags_by_gsm,
            active_row_idx=active_row_idx,
            flag_summaries=flag_summaries,
            primary_failures=primary_failures,
        )
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
            _render_details_modal(details, paths.suggestions_present, edit_mode)


run_app()
