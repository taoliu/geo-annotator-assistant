"""CLI entrypoint for read-only output summarization."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from agent.gse_postpass import apply_gse_field_values_summary
from ui.loaders import load_curation_jsonl, load_jsonl
from ui.overrides import (
    apply_overrides_to_record,
    load_overrides_jsonl,
    overrides_for_gsm,
)
from ui.paths import InputPaths, InputScanResult, resolve_input_directory
from ui.schema import CANONICAL_FIELDS

_DEFAULT_IGNORE_VALUES = ("Unknown", "None", "No", "Healthy")
_GSM_CSV_COLUMNS = ("gse_accession", "gsm_accession", *CANONICAL_FIELDS)
_GSE_CSV_COLUMNS = ("gse_accession", *CANONICAL_FIELDS)


class _ArgumentParser(argparse.ArgumentParser):
    """ArgumentParser that exits with code 1 on usage errors."""

    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        self.exit(1, f"error: {message}\n")


def build_parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(
        description=(
            "Summarize existing output artifacts into GSM and GSE CSV files "
            "without rerunning backend inference."
        )
    )
    parser.add_argument(
        "--input-dir",
        required=True,
        help="Directory containing one or more GSE output directories.",
    )
    parser.add_argument(
        "--overrides",
        help=(
            "Optional overrides.jsonl path. When provided, this file is used "
            "instead of auto-detected per-GSE overrides."
        ),
    )
    parser.add_argument(
        "--output-dir",
        help="Directory where CSV outputs are written (default: --input-dir).",
    )
    parser.add_argument(
        "--gsm-csv",
        default="gsm_annotations.csv",
        help="Output GSM CSV filename (default: gsm_annotations.csv).",
    )
    parser.add_argument(
        "--gse-csv",
        default="gse_summary.csv",
        help="Output GSE CSV filename (default: gse_summary.csv).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on missing/unreadable GSE artifacts instead of warning and skipping.",
    )
    return parser


def _iter_scan_paths(scan: InputScanResult) -> list[tuple[str, InputPaths]]:
    if scan.mode == "single":
        if scan.single_paths is None:
            return []
        return [(scan.input_dir.name, scan.single_paths)]
    return [
        (gse_name, scan.gse_paths[gse_name])
        for gse_name in sorted(scan.gse_paths.keys())
    ]


def _resolve_gse_accession(
    curation_records: list[dict[str, Any]],
    fallback: str,
) -> str:
    values = {
        record["gse_accession"]
        for record in curation_records
        if isinstance(record.get("gse_accession"), str) and record.get("gse_accession")
    }
    if len(values) == 1:
        return next(iter(values))
    if fallback:
        return fallback
    return "Unknown"


def _stringify_csv_value(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def _render_gse_summary_value(value: object) -> str:
    if isinstance(value, list):
        rendered = ", ".join(str(item) for item in value if item)
    else:
        rendered = str(value) if value is not None else ""
    return rendered or ""


def _load_ignore_values(paths: InputPaths) -> list[str]:
    gse_values_path = paths.gse_field_values_path
    if not gse_values_path.is_file():
        return list(_DEFAULT_IGNORE_VALUES)
    records = load_jsonl(str(gse_values_path))
    if not records:
        return list(_DEFAULT_IGNORE_VALUES)
    first = records[0]
    if not isinstance(first, dict):
        return list(_DEFAULT_IGNORE_VALUES)
    raw = first.get("ignore_values")
    if isinstance(raw, list):
        values = [value for value in raw if isinstance(value, str)]
        if values:
            return values
    return list(_DEFAULT_IGNORE_VALUES)


def _build_gsm_rows(
    curation_records: list[dict[str, Any]],
    overrides: dict,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for record in curation_records:
        gse = record["gse_accession"]
        gsm = record["gsm_accession"]
        selected = overrides_for_gsm(overrides, gse, gsm)
        effective_fields = apply_overrides_to_record(record, selected)
        if effective_fields is None:
            continue
        row: dict[str, object] = {
            "gse_accession": gse,
            "gsm_accession": gsm,
        }
        for field in CANONICAL_FIELDS:
            row[field] = effective_fields.get(field, "")
        rows.append(row)
    return rows


def _build_gse_rows(
    gsm_rows: list[dict[str, object]],
    ignore_values_by_gse: dict[str, list[str]],
) -> list[dict[str, str]]:
    rows_by_gse: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in gsm_rows:
        gse_accession = str(row.get("gse_accession", "Unknown"))
        normalized: dict[str, Any] = {"gse_accession": gse_accession}
        for field in CANONICAL_FIELDS:
            normalized[field] = _stringify_csv_value(row.get(field, ""))
        rows_by_gse[gse_accession].append(normalized)

    gse_rows: list[dict[str, str]] = []
    for gse_accession in sorted(rows_by_gse):
        ignore_values = ignore_values_by_gse.get(
            gse_accession, list(_DEFAULT_IGNORE_VALUES)
        )
        summary_cfg = {
            "postpass": {
                "gse_consistency": {
                    "enabled": True,
                    "fields": list(CANONICAL_FIELDS),
                    "ignore_values": ignore_values,
                }
            }
        }
        summary = apply_gse_field_values_summary(rows_by_gse[gse_accession], summary_cfg)
        fields_raw = summary.get("fields") if isinstance(summary, dict) else {}
        fields = fields_raw if isinstance(fields_raw, dict) else {}
        row: dict[str, str] = {"gse_accession": gse_accession}
        for field in CANONICAL_FIELDS:
            row[field] = _render_gse_summary_value(fields.get(field, []))
        gse_rows.append(row)
    return gse_rows


def _write_csv(
    path: Path,
    header: tuple[str, ...],
    rows: list[dict[str, object]] | list[dict[str, str]],
) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(list(header))
        for row in rows:
            writer.writerow([_stringify_csv_value(row.get(column, "")) for column in header])


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        input_dir = Path(args.input_dir)
        output_dir = Path(args.output_dir) if args.output_dir else input_dir
        explicit_overrides = Path(args.overrides) if args.overrides else None

        print(f"INFO: summarize: scanning {input_dir}", file=sys.stderr)
        scan = resolve_input_directory(str(input_dir))

        if scan.skipped:
            skip_items = sorted(scan.skipped.items())
            if args.strict:
                rendered = "; ".join(f"{name}: {reason}" for name, reason in skip_items)
                raise ValueError(f"strict mode: skipped GSE directories: {rendered}")
            for name, reason in skip_items:
                print(
                    f"WARNING: summarize: skipping {name}: {reason}",
                    file=sys.stderr,
                )

        if explicit_overrides is not None and not explicit_overrides.is_file():
            raise FileNotFoundError(f"Overrides file not found: {explicit_overrides}")

        gsm_rows: list[dict[str, object]] = []
        ignore_values_by_gse: dict[str, list[str]] = {}
        auto_override_paths_used: set[str] = set()
        explicit_overrides_used = False

        for gse_name, paths in _iter_scan_paths(scan):
            try:
                curation_records = load_curation_jsonl(str(paths.curation_path))
                gse_accession = _resolve_gse_accession(curation_records, gse_name)
                try:
                    ignore_values_by_gse[gse_accession] = _load_ignore_values(paths)
                except Exception as exc:
                    print(
                        f"WARNING: summarize: invalid gse_field_values.jsonl for {gse_accession}; using default ignore values ({exc})",
                        file=sys.stderr,
                    )
                    ignore_values_by_gse[gse_accession] = list(_DEFAULT_IGNORE_VALUES)

                overrides = {}
                if explicit_overrides is not None:
                    overrides = load_overrides_jsonl(
                        str(explicit_overrides), gse_accession
                    )
                    explicit_overrides_used = True
                else:
                    auto_path = paths.input_dir / "overrides.jsonl"
                    if auto_path.is_file():
                        try:
                            overrides = load_overrides_jsonl(str(auto_path), gse_accession)
                            auto_override_paths_used.add(str(auto_path))
                        except Exception as exc:
                            if args.strict:
                                raise
                            print(
                                f"WARNING: summarize: could not apply overrides for {gse_accession}: {exc}",
                                file=sys.stderr,
                            )
                            overrides = {}

                gsm_rows.extend(_build_gsm_rows(curation_records, overrides))
            except Exception as exc:
                if args.strict:
                    raise ValueError(f"{gse_name}: {exc}") from exc
                print(
                    f"WARNING: summarize: skipping {gse_name}: {exc}",
                    file=sys.stderr,
                )

        gsm_rows.sort(
            key=lambda row: (
                str(row.get("gse_accession", "")),
                str(row.get("gsm_accession", "")),
            )
        )
        gse_rows = _build_gse_rows(gsm_rows, ignore_values_by_gse)

        n_gse = len({str(row.get("gse_accession", "")) for row in gsm_rows})
        print(
            f"INFO: summarize: loaded {len(gsm_rows)} GSM records across {n_gse} GSEs",
            file=sys.stderr,
        )
        if explicit_overrides_used and explicit_overrides is not None:
            print(
                f"INFO: summarize: applied overrides from {explicit_overrides}",
                file=sys.stderr,
            )
        elif auto_override_paths_used:
            print(
                "INFO: summarize: applied overrides from auto-detected overrides.jsonl "
                f"({len(auto_override_paths_used)} file(s))",
                file=sys.stderr,
            )
        else:
            print("INFO: summarize: applied overrides from none", file=sys.stderr)

        output_dir.mkdir(parents=True, exist_ok=True)
        gsm_csv_path = output_dir / args.gsm_csv
        gse_csv_path = output_dir / args.gse_csv
        _write_csv(gsm_csv_path, _GSM_CSV_COLUMNS, gsm_rows)
        _write_csv(gse_csv_path, _GSE_CSV_COLUMNS, gse_rows)
        print(f"INFO: summarize: wrote {gsm_csv_path}", file=sys.stderr)
        print(f"INFO: summarize: wrote {gse_csv_path}", file=sys.stderr)
    except Exception as exc:
        print(f"runtime error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc


if __name__ == "__main__":
    main()
