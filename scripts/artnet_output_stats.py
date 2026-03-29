#!/usr/bin/env python3
"""Summarize read-only run artifacts under an output directory such as out/artnet."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

EXACT_LABEL_OR_ID_MATCH_TYPES = {
    "exact",
    "label_exact",
    "label_norm_exact",
    "term_id_exact",
}
EXACT_SYNONYM_MATCH_TYPES = {
    "synonym",
    "synonym_exact",
    "synonym_norm_exact",
}


def _iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSON") from exc
            if not isinstance(record, dict):
                raise ValueError(f"{path}:{line_number}: expected JSON object")
            yield record


def _sorted_counter(counter: Counter[str]) -> dict[str, int]:
    return {key: counter[key] for key, _ in sorted(counter.items(), key=lambda item: (-item[1], item[0]))}


def _sorted_nested_counter(counter_map: dict[str, Counter[str]]) -> dict[str, dict[str, int]]:
    return {
        key: _sorted_counter(counter_map[key])
        for key in sorted(counter_map)
    }


def _is_ontology_canonicalization(event: dict[str, Any]) -> bool:
    return bool(event.get("source")) or bool(event.get("term_id"))


def _value_changed(original_value: Any, canonical_value: Any) -> bool:
    return str(original_value).strip() != str(canonical_value).strip()


def _classify_match_route(status: Any, match_type: Any) -> str | None:
    if status != "MATCHED" or not isinstance(match_type, str) or not match_type:
        return None
    if match_type in EXACT_LABEL_OR_ID_MATCH_TYPES:
        return "exact_label_or_id"
    if match_type in EXACT_SYNONYM_MATCH_TYPES:
        return "exact_synonym"
    return "semantic_threshold"


def aggregate_output_dir(input_dir: Path) -> dict[str, Any]:
    if not input_dir.exists():
        raise FileNotFoundError(f"input directory does not exist: {input_dir}")
    if not input_dir.is_dir():
        raise NotADirectoryError(f"input path is not a directory: {input_dir}")

    gse_dirs = sorted(
        path for path in input_dir.iterdir() if path.is_dir() and path.name.startswith("GSE")
    )

    decisions: Counter[str] = Counter()
    top_level_flags: Counter[str] = Counter()
    primary_failures: Counter[str] = Counter()
    ontology_status_by_field: dict[str, Counter[str]] = defaultdict(Counter)
    repair_events_by_field: Counter[str] = Counter()
    fallback_events_by_field: Counter[str] = Counter()
    ontology_canonicalizations_by_field: Counter[str] = Counter()
    ontology_canonicalizations_by_match_type: Counter[str] = Counter()
    ontology_match_routes: Counter[str] = Counter()
    ontology_match_routes_by_field: dict[str, Counter[str]] = defaultdict(Counter)
    field_flag_cells_by_field: Counter[str] = Counter()
    field_flag_events_by_field: Counter[str] = Counter()
    field_flag_names: Counter[str] = Counter()
    gse_suggestions_by_reason: Counter[str] = Counter()
    gse_suggestions_by_field: Counter[str] = Counter()
    gse_outlier_flags_by_field: Counter[str] = Counter()

    total_gsms = 0
    total_llm_calls = 0
    total_proposal_calls = 0
    total_repair_llm_calls = 0
    total_cache_hits = 0
    max_llm_calls_single_gsm = 0

    gsms_flagged = 0
    gsms_with_any_top_level_flags = 0
    gsms_with_any_repair_activity = 0
    gsms_with_llm_repair_attempts = 0
    gsms_with_deterministic_fallbacks = 0
    repaired_then_accepted = 0
    repaired_then_flagged = 0
    llm_repair_then_accepted = 0
    llm_repair_then_flagged = 0
    fallback_only_then_accepted = 0
    fallback_only_then_flagged = 0
    salvage_only_then_accepted = 0
    salvage_only_then_flagged = 0
    total_repair_history_events = 0
    total_llm_repair_events = 0
    total_fallback_events = 0
    gsms_with_terminal_fallbacks = 0
    total_terminal_fallback_events = 0
    terminal_fallbacks_by_field: Counter[str] = Counter()
    gsms_with_ontology_canonicalization = 0
    gsms_with_changed_ontology_canonicalization = 0
    total_ontology_canonicalization_events = 0
    total_changed_ontology_canonicalization_events = 0
    gsms_with_any_field_flags = 0
    total_field_flag_cells = 0
    total_field_flag_events = 0
    total_gse_suggestions = 0

    processed_gse_dirs: list[str] = []
    skipped_gse_dirs: list[str] = []

    for gse_dir in gse_dirs:
        audit_path = gse_dir / "audit.jsonl"
        if not audit_path.exists():
            skipped_gse_dirs.append(gse_dir.name)
            continue

        processed_gse_dirs.append(gse_dir.name)
        for record in _iter_jsonl(audit_path):
            total_gsms += 1

            final_decision = str(record.get("final_decision") or record.get("rationale", {}).get("final_decision") or "UNKNOWN")
            decisions[final_decision] += 1
            if final_decision == "FLAGGED":
                gsms_flagged += 1

            flags = record.get("flags") or record.get("rationale", {}).get("flags") or []
            if isinstance(flags, list) and flags:
                gsms_with_any_top_level_flags += 1
                for flag in flags:
                    if not isinstance(flag, str):
                        continue
                    top_level_flags[flag] += 1
                    if flag.startswith("gse_outlier_"):
                        gse_outlier_flags_by_field[flag.removeprefix("gse_outlier_")] += 1

            rationale = record.get("rationale")
            if not isinstance(rationale, dict):
                rationale = {}

            n_llm_calls = rationale.get("n_llm_calls")
            if not isinstance(n_llm_calls, int):
                n_llm_calls = len(record.get("llm_raw_outputs") or [])
            total_llm_calls += n_llm_calls
            if n_llm_calls > 0:
                total_proposal_calls += 1
            if n_llm_calls > 1:
                total_repair_llm_calls += n_llm_calls - 1
            if n_llm_calls > max_llm_calls_single_gsm:
                max_llm_calls_single_gsm = n_llm_calls

            cache_hits = record.get("llm_cache_hits") or []
            if isinstance(cache_hits, list):
                total_cache_hits += sum(1 for hit in cache_hits if hit is True)

            primary_failure = rationale.get("primary_failure")
            if isinstance(primary_failure, str) and primary_failure:
                primary_failures[primary_failure] += 1

            ontology_statuses = rationale.get("ontology_status_by_field") or {}
            if isinstance(ontology_statuses, dict):
                for field, status in ontology_statuses.items():
                    if isinstance(field, str) and isinstance(status, str) and status:
                        ontology_status_by_field[field][status] += 1

            validation = record.get("validation")
            if isinstance(validation, dict):
                ontology_matches = validation.get("ontology_matches")
                if isinstance(ontology_matches, dict):
                    for field, match in ontology_matches.items():
                        if not isinstance(field, str) or not isinstance(match, dict):
                            continue
                        route = _classify_match_route(
                            match.get("status"),
                            match.get("match_type"),
                        )
                        if route is None:
                            continue
                        ontology_match_routes[route] += 1
                        ontology_match_routes_by_field[field][route] += 1

            repair_history = record.get("repair_history") or []
            if isinstance(repair_history, list) and repair_history:
                gsms_with_any_repair_activity += 1
                total_repair_history_events += len(repair_history)
                if final_decision == "ACCEPT":
                    repaired_then_accepted += 1
                elif final_decision == "FLAGGED":
                    repaired_then_flagged += 1

                record_has_llm_repair = False
                record_has_fallback = False
                record_has_salvage_only = False
                for event in repair_history:
                    if not isinstance(event, dict):
                        continue
                    field = event.get("field")
                    if isinstance(field, str) and field:
                        repair_events_by_field[field] += 1
                    if event.get("repair_template"):
                        total_llm_repair_events += 1
                        record_has_llm_repair = True
                    if "fallback_value" in event:
                        total_fallback_events += 1
                        record_has_fallback = True
                        if isinstance(field, str) and field:
                            fallback_events_by_field[field] += 1
                if not record_has_llm_repair and not record_has_fallback:
                    record_has_salvage_only = True
                if record_has_llm_repair:
                    gsms_with_llm_repair_attempts += 1
                    if final_decision == "ACCEPT":
                        llm_repair_then_accepted += 1
                    elif final_decision == "FLAGGED":
                        llm_repair_then_flagged += 1
                if record_has_fallback:
                    gsms_with_deterministic_fallbacks += 1
                if record_has_fallback and not record_has_llm_repair:
                    if final_decision == "ACCEPT":
                        fallback_only_then_accepted += 1
                    elif final_decision == "FLAGGED":
                        fallback_only_then_flagged += 1
                if record_has_salvage_only:
                    if final_decision == "ACCEPT":
                        salvage_only_then_accepted += 1
                    elif final_decision == "FLAGGED":
                        salvage_only_then_flagged += 1

            terminal_fallback_fields = rationale.get("terminal_fallback_fields") or []
            if isinstance(terminal_fallback_fields, list) and terminal_fallback_fields:
                gsms_with_terminal_fallbacks += 1
                total_terminal_fallback_events += len(terminal_fallback_fields)
                for field in terminal_fallback_fields:
                    if isinstance(field, str):
                        terminal_fallbacks_by_field[field] += 1

            canonicalizations = record.get("canonicalizations") or []
            if isinstance(canonicalizations, dict):
                canonicalization_iterable = canonicalizations.values()
            elif isinstance(canonicalizations, list):
                canonicalization_iterable = canonicalizations
            else:
                canonicalization_iterable = []

            record_has_ontology_canonicalization = False
            record_has_changed_ontology_canonicalization = False
            for event in canonicalization_iterable:
                if not isinstance(event, dict) or not _is_ontology_canonicalization(event):
                    continue
                total_ontology_canonicalization_events += 1
                record_has_ontology_canonicalization = True

                field = event.get("field")
                if isinstance(field, str) and field:
                    ontology_canonicalizations_by_field[field] += 1

                match_type = event.get("match_type")
                if isinstance(match_type, str) and match_type:
                    ontology_canonicalizations_by_match_type[match_type] += 1

                if _value_changed(event.get("original_value"), event.get("canonical_value")):
                    total_changed_ontology_canonicalization_events += 1
                    record_has_changed_ontology_canonicalization = True

            if record_has_ontology_canonicalization:
                gsms_with_ontology_canonicalization += 1
            if record_has_changed_ontology_canonicalization:
                gsms_with_changed_ontology_canonicalization += 1

        evidence_path = gse_dir / "evidence.jsonl"
        if evidence_path.exists():
            for record in _iter_jsonl(evidence_path):
                evidence_by_field = record.get("evidence_by_field")
                if not isinstance(evidence_by_field, dict):
                    continue
                gsm_has_any_field_flags = False
                for field, field_evidence in evidence_by_field.items():
                    if not isinstance(field, str) or not isinstance(field_evidence, dict):
                        continue
                    flags = field_evidence.get("flags") or []
                    if not isinstance(flags, list) or not flags:
                        continue
                    gsm_has_any_field_flags = True
                    total_field_flag_cells += 1
                    field_flag_cells_by_field[field] += 1
                    total_field_flag_events += len(flags)
                    field_flag_events_by_field[field] += len(flags)
                    for flag in flags:
                        if isinstance(flag, str):
                            field_flag_names[flag] += 1
                if gsm_has_any_field_flags:
                    gsms_with_any_field_flags += 1

        suggestions_path = gse_dir / "suggestions.jsonl"
        if suggestions_path.exists():
            for record in _iter_jsonl(suggestions_path):
                total_gse_suggestions += 1
                field = record.get("field")
                reason = record.get("reason")
                if isinstance(field, str) and field:
                    gse_suggestions_by_field[field] += 1
                if isinstance(reason, str) and reason:
                    gse_suggestions_by_reason[reason] += 1

    llm_summary = {
        "total_calls": total_llm_calls,
        "proposal_calls": total_proposal_calls,
        "repair_calls": total_repair_llm_calls,
        "cache_hits": total_cache_hits,
        "uncached_calls": total_llm_calls - total_cache_hits,
        "avg_calls_per_gsm": round(total_llm_calls / total_gsms, 3) if total_gsms else 0.0,
        "max_calls_for_single_gsm": max_llm_calls_single_gsm,
    }

    return {
        "input_dir": str(input_dir),
        "gse_dirs_discovered": len(gse_dirs),
        "gse_dirs_processed": len(processed_gse_dirs),
        "gse_dirs_skipped": len(skipped_gse_dirs),
        "skipped_gse_dirs": skipped_gse_dirs,
        "gsm_records": total_gsms,
        "final_decisions": _sorted_counter(decisions),
        "flagged_gsms": gsms_flagged,
        "gsms_with_any_top_level_flags": gsms_with_any_top_level_flags,
        "top_level_flags": _sorted_counter(top_level_flags),
        "primary_failures": _sorted_counter(primary_failures),
        "llm": llm_summary,
        "repairs": {
            "gsms_with_any_repair_activity": gsms_with_any_repair_activity,
            "gsms_with_llm_repair_attempts": gsms_with_llm_repair_attempts,
            "gsms_with_deterministic_fallbacks": gsms_with_deterministic_fallbacks,
            "repaired_then_accepted": repaired_then_accepted,
            "repaired_then_flagged": repaired_then_flagged,
            "llm_repair_then_accepted": llm_repair_then_accepted,
            "llm_repair_then_flagged": llm_repair_then_flagged,
            "fallback_only_then_accepted": fallback_only_then_accepted,
            "fallback_only_then_flagged": fallback_only_then_flagged,
            "salvage_only_then_accepted": salvage_only_then_accepted,
            "salvage_only_then_flagged": salvage_only_then_flagged,
            "repair_history_events": total_repair_history_events,
            "llm_repair_events": total_llm_repair_events,
            "fallback_events": total_fallback_events,
            "events_by_field": _sorted_counter(repair_events_by_field),
            "fallbacks_by_field": _sorted_counter(fallback_events_by_field),
        },
        "ontology": {
            "status_by_field": _sorted_nested_counter(ontology_status_by_field),
            "gsms_with_ontology_canonicalization": gsms_with_ontology_canonicalization,
            "gsms_with_changed_ontology_canonicalization": gsms_with_changed_ontology_canonicalization,
            "canonicalization_events": total_ontology_canonicalization_events,
            "changed_value_events": total_changed_ontology_canonicalization_events,
            "canonicalizations_by_field": _sorted_counter(ontology_canonicalizations_by_field),
            "canonicalizations_by_match_type": _sorted_counter(ontology_canonicalizations_by_match_type),
            "matched_routes": _sorted_counter(ontology_match_routes),
            "matched_routes_by_field": _sorted_nested_counter(ontology_match_routes_by_field),
        },
        "terminal_fallbacks": {
            "gsms_with_terminal_fallbacks": gsms_with_terminal_fallbacks,
            "events": total_terminal_fallback_events,
            "by_field": _sorted_counter(terminal_fallbacks_by_field),
        },
        "field_diagnostics": {
            "gsms_with_any_field_flags": gsms_with_any_field_flags,
            "flagged_field_cells": total_field_flag_cells,
            "flag_events": total_field_flag_events,
            "flagged_cells_by_field": _sorted_counter(field_flag_cells_by_field),
            "flag_events_by_field": _sorted_counter(field_flag_events_by_field),
            "flag_names": _sorted_counter(field_flag_names),
        },
        "gse_advisory": {
            "suggestion_events": total_gse_suggestions,
            "suggestions_by_reason": _sorted_counter(gse_suggestions_by_reason),
            "suggestions_by_field": _sorted_counter(gse_suggestions_by_field),
            "gse_outlier_flags_by_field": _sorted_counter(gse_outlier_flags_by_field),
        },
    }


def _format_counter_lines(counter_map: dict[str, int], *, top: int, indent: str = "  ") -> list[str]:
    if not counter_map:
        return [f"{indent}(none)"]
    lines: list[str] = []
    for index, (key, value) in enumerate(counter_map.items()):
        if index >= top:
            break
        lines.append(f"{indent}{key}: {value}")
    return lines


def format_text_summary(stats: dict[str, Any], *, top: int = 10) -> str:
    lines = [
        "ARTNet Output Statistics",
        f"Input dir: {stats['input_dir']}",
        (
            "GSE directories: "
            f"{stats['gse_dirs_discovered']} discovered, "
            f"{stats['gse_dirs_processed']} processed, "
            f"{stats['gse_dirs_skipped']} skipped"
        ),
        f"GSM records: {stats['gsm_records']}",
        "",
        "Final decisions:",
        *_format_counter_lines(stats["final_decisions"], top=top),
        f"  flagged_gsms: {stats['flagged_gsms']}",
        "",
        "LLM usage:",
        f"  total_calls: {stats['llm']['total_calls']}",
        f"  proposal_calls: {stats['llm']['proposal_calls']}",
        f"  repair_calls: {stats['llm']['repair_calls']}",
        f"  cache_hits: {stats['llm']['cache_hits']}",
        f"  uncached_calls: {stats['llm']['uncached_calls']}",
        f"  avg_calls_per_gsm: {stats['llm']['avg_calls_per_gsm']}",
        f"  max_calls_for_single_gsm: {stats['llm']['max_calls_for_single_gsm']}",
        "",
        "Repairs:",
        f"  gsms_with_any_repair_activity: {stats['repairs']['gsms_with_any_repair_activity']}",
        f"  gsms_with_llm_repair_attempts: {stats['repairs']['gsms_with_llm_repair_attempts']}",
        f"  gsms_with_deterministic_fallbacks: {stats['repairs']['gsms_with_deterministic_fallbacks']}",
        f"  repaired_then_accepted: {stats['repairs']['repaired_then_accepted']}",
        f"  repaired_then_flagged: {stats['repairs']['repaired_then_flagged']}",
        f"  llm_repair_then_accepted: {stats['repairs']['llm_repair_then_accepted']}",
        f"  llm_repair_then_flagged: {stats['repairs']['llm_repair_then_flagged']}",
        f"  repair_history_events: {stats['repairs']['repair_history_events']}",
        f"  llm_repair_events: {stats['repairs']['llm_repair_events']}",
        f"  fallback_events: {stats['repairs']['fallback_events']}",
        "",
        "Ontology normalization:",
        f"  gsms_with_ontology_canonicalization: {stats['ontology']['gsms_with_ontology_canonicalization']}",
        (
            "  gsms_with_changed_ontology_canonicalization: "
            f"{stats['ontology']['gsms_with_changed_ontology_canonicalization']}"
        ),
        f"  canonicalization_events: {stats['ontology']['canonicalization_events']}",
        f"  changed_value_events: {stats['ontology']['changed_value_events']}",
        f"  exact_label_or_id_matches: {stats['ontology']['matched_routes'].get('exact_label_or_id', 0)}",
        f"  exact_synonym_matches: {stats['ontology']['matched_routes'].get('exact_synonym', 0)}",
        f"  semantic_threshold_matches: {stats['ontology']['matched_routes'].get('semantic_threshold', 0)}",
        "",
        "Terminal fallbacks:",
        f"  gsms_with_terminal_fallbacks: {stats['terminal_fallbacks']['gsms_with_terminal_fallbacks']}",
        f"  events: {stats['terminal_fallbacks']['events']}",
        "",
        "Field diagnostics:",
        f"  gsms_with_any_field_flags: {stats['field_diagnostics']['gsms_with_any_field_flags']}",
        f"  flagged_field_cells: {stats['field_diagnostics']['flagged_field_cells']}",
        f"  flag_events: {stats['field_diagnostics']['flag_events']}",
        "",
        "Top level flags:",
        *_format_counter_lines(stats["top_level_flags"], top=top),
        "",
        "Primary failures:",
        *_format_counter_lines(stats["primary_failures"], top=top),
        "",
        "Field diagnostics by flag:",
        *_format_counter_lines(stats["field_diagnostics"]["flag_names"], top=top),
        "",
        "GSE advisory suggestions:",
        f"  suggestion_events: {stats['gse_advisory']['suggestion_events']}",
    ]

    if stats["gse_dirs_skipped"]:
        skipped = ", ".join(stats["skipped_gse_dirs"][:top])
        lines.extend(["", f"Skipped GSE directories: {skipped}"])

    return "\n".join(lines)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Aggregate read-only statistics from a run output directory such as out/artnet."
    )
    parser.add_argument(
        "--input-dir",
        default="out/artnet",
        help="Run output directory containing GSE* subdirectories (default: out/artnet).",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Maximum number of counter entries to show in text mode (default: 10).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    stats = aggregate_output_dir(Path(args.input_dir))
    if args.format == "json":
        print(json.dumps(stats, indent=2, sort_keys=True))
    else:
        print(format_text_summary(stats, top=max(args.top, 1)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
