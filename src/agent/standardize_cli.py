"""CLI entrypoint for standardize-terms."""

from __future__ import annotations

import argparse
import sys

from agent.config import load_config
from agent.standardize_terms import GROUNDED_FIELDS, standardize_terms_jsonl


class _ArgumentParser(argparse.ArgumentParser):
    """ArgumentParser that exits with code 1 on usage errors."""

    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        self.exit(1, f"error: {message}\n")


def parse_fields_arg(fields_arg: str | None) -> list[str]:
    if not fields_arg:
        return list(GROUNDED_FIELDS)
    raw_fields = [field.strip() for field in fields_arg.split(",") if field.strip()]
    if not raw_fields:
        return list(GROUNDED_FIELDS)
    invalid = [field for field in raw_fields if field not in GROUNDED_FIELDS]
    if invalid:
        invalid_list = ", ".join(invalid)
        raise ValueError(f"Unsupported field(s) for grounding: {invalid_list}")
    seen = set()
    ordered: list[str] = []
    for field in raw_fields:
        if field in seen:
            continue
        ordered.append(field)
        seen.add(field)
    return ordered


def _parse_optional_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError(f"Invalid boolean value: {value!r}")


def resolve_output_paths(
    input_path: str,
    output_path: str | None,
    audit_path: str | None,
) -> tuple[str, str]:
    resolved_output = output_path or f"{input_path}.standardized.jsonl"
    resolved_audit = audit_path or f"{resolved_output}.audit.jsonl"
    return resolved_output, resolved_audit


def _examples_text() -> str:
    return "\n".join(
        [
            "Examples:",
            "  gaa-annotate standardize-terms -i curated.jsonl",
            "  gaa-annotate standardize-terms -i curated.jsonl -o out.jsonl -f disease,cell_line",
        ]
    )


def _defaults_text() -> str:
    fields_default = ",".join(GROUNDED_FIELDS)
    return "\n".join(
        [
            "Defaults:",
            "  output: <input>.standardized.jsonl",
            "  audit: <output>.audit.jsonl",
            f"  fields: {fields_default}",
            "  canonicalize: respect config",
        ]
    )


def build_parser() -> argparse.ArgumentParser:
    description = "Standardize curator-provided GSM annotations."
    epilog = "\n".join([_defaults_text(), _examples_text()])
    parser = _ArgumentParser(
        description=description,
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="Path to input JSONL.",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Path to output JSONL (default: <input>.standardized.jsonl).",
    )
    parser.add_argument(
        "-a",
        "--audit",
        help="Path to audit JSONL (default: <output>.audit.jsonl).",
    )
    parser.add_argument(
        "-c",
        "--config",
        required=True,
        help="Path to YAML config file.",
    )
    parser.add_argument(
        "-f",
        "--fields",
        help=(
            "Comma-separated grounded fields "
            "(default: data_type,tissue_type,cell_line,disease)."
        ),
    )
    parser.add_argument(
        "--canonicalize",
        type=_parse_optional_bool,
        default=None,
        help=(
            "Override canonicalization (true/false); "
            "default: respect config."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        config = load_config(args.config)
        fields = parse_fields_arg(args.fields)
        output_path, audit_path = resolve_output_paths(
            args.input,
            args.output,
            args.audit,
        )
        standardize_terms_jsonl(
            args.input,
            output_path,
            audit_path,
            config,
            fields=fields,
            canonicalize=args.canonicalize,
        )
    except Exception as exc:
        print(f"runtime error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
