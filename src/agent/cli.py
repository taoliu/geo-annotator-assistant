"""CLI entrypoint for geo-gsm-annotator-agent."""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path

from agent.config import load_config
from agent.runtime_trace import (
    log_gse_outputs_written,
    log_gse_start_processing,
    tracing_scope,
)
from agent.run_batch import run_batch
from agent.run_gse import (
    run_gse_from_accession,
    run_gse_from_jsonl,
    run_gse_from_soft_file,
)
from agent.run_single import run_single_gsm
from agent.suggestions import build_gse_suggestions
from agent import standardize_cli
from agent.writer import write_run_outputs
from llm.factory import create_llm_client
from ingest.soft_to_context_jsonl import GseSoftSkipError


class _ArgumentParser(argparse.ArgumentParser):
    """ArgumentParser that exits with code 1 on usage errors."""

    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        self.exit(1, f"error: {message}\n")


_OUTPUT_DIR_SENTINEL = object()


def _read_gsm_file(path: str) -> list[str]:
    gsm_path = Path(path)
    if not gsm_path.is_file():
        raise ValueError(f"GSM file not found: {path}")

    gsm_ids: list[str] = []
    with gsm_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            gsm_ids.append(stripped)

    return gsm_ids


def _read_gse_file(path: str) -> list[str]:
    gse_path = Path(path)
    if not gse_path.is_file():
        raise ValueError(f"GSE file not found: {path}")

    gse_ids: list[str] = []
    seen: set[str] = set()
    with gse_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if stripped in seen:
                continue
            seen.add(stripped)
            gse_ids.append(stripped)

    if not gse_ids:
        raise ValueError(f"No GSE accessions found in file: {path}")

    return gse_ids


def _sanitize_batch_label(label: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", label).strip("_")
    return cleaned or "gse_batch"


def _default_gse_batch_output_dir(gse_file: str, gse_ids: list[str]) -> str:
    stem = Path(gse_file).stem
    label = _sanitize_batch_label(stem)
    digest = hashlib.sha1("\n".join(gse_ids).encode("utf-8")).hexdigest()[:8]
    return str(Path("outputs") / f"{label}_{len(gse_ids)}_{digest}")


def _print_summary(
    summary: dict[str, int],
    output_paths: dict[str, str] | None,
    dry_run: bool,
) -> None:
    print(f"Total: {summary['n_total']}")
    print(f"Accepted: {summary['n_accepted']}")
    print(f"Flagged: {summary['n_flagged']}")
    if dry_run:
        print("Dry-run: no files written")
        return
    if output_paths:
        print(f"Annotations: {output_paths.get('annotations', '')}")
        print(f"Audit: {output_paths.get('audit', '')}")
        print(f"Flagged: {output_paths.get('flagged', '')}")


def _resolve_output_dir(
    base_dir: str,
    annotations: list[dict],
    use_gse_subdir: bool,
) -> str:
    if not use_gse_subdir:
        return base_dir
    gse_values = {
        record.get("gse_accession")
        for record in annotations
        if record.get("gse_accession")
    }
    if len(gse_values) == 1:
        gse_accession = next(iter(gse_values))
        return str(Path(base_dir) / gse_accession)
    return base_dir


def _collect_gse_accessions(annotations: list[dict]) -> list[str]:
    gse_values = {
        str(record.get("gse_accession"))
        for record in annotations
        if record.get("gse_accession")
    }
    return sorted(gse_values)


def _build_parser() -> argparse.ArgumentParser:
    description = "Run the GEO GSM annotator agent."
    epilog = "\n".join(
        [
            "Subcommands:",
            "  standardize-terms  Standardize curator-provided GSM annotations.",
            "Use `geo-gsm-annotate standardize-terms --help` for details.",
        ]
    )
    parser = _ArgumentParser(
        description=description,
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--gsm", help="Single GSM identifier to process.")
    group.add_argument("--gsm-file", help="Path to a file containing GSM identifiers.")
    group.add_argument("--jsonl", help="Path to JSONL context records.")
    group.add_argument("--gse", help="GSE accession to process.")
    group.add_argument(
        "--gse-file",
        help="Path to a file containing GSE accessions (one per line).",
    )
    group.add_argument(
        "--gse-soft",
        help="Path to a local GSE SOFT file (.soft or .soft.gz).",
    )
    parser.add_argument(
        "--output-dir",
        default=_OUTPUT_DIR_SENTINEL,
        help="Directory for outputs.",
    )
    parser.add_argument("--config", required=True, help="Path to YAML config file.")
    parser.add_argument(
        "--emit-suggestions",
        action="store_true",
        help="Emit suggestions.jsonl for cross-GSM advisory hints.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run the pipeline but skip writing output files.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Emit runtime milestone tracing to stderr for pipeline execution steps.",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parsed_argv = list(argv) if argv is not None else sys.argv[1:]
    if parsed_argv and parsed_argv[0] == "standardize-terms":
        standardize_cli.main(parsed_argv[1:])
        return

    parser = _build_parser()
    args = parser.parse_args(parsed_argv)

    try:
        with tracing_scope(args.verbose):
            config = load_config(args.config)

            gse_report = None
            gse_values = None
            output_dir_arg = args.output_dir
            output_base_dir = None
            if args.gse_file:
                gse_ids = _read_gse_file(args.gse_file)
                output_base_dir = (
                    _default_gse_batch_output_dir(args.gse_file, gse_ids)
                    if output_dir_arg is _OUTPUT_DIR_SENTINEL
                    else output_dir_arg
                )
            else:
                output_base_dir = (
                    "outputs"
                    if output_dir_arg is _OUTPUT_DIR_SENTINEL
                    else output_dir_arg
                )

            llm_client = None
            if args.gse_file or args.gse or args.gse_soft or args.jsonl:
                llm_cfg = (
                    config.get("llm", {}) if isinstance(config.get("llm"), dict) else {}
                )
                llm_transport = llm_cfg.get("transport") or llm_cfg.get("mode", "stub")
                if llm_transport == "local_transformers":
                    llm_client = create_llm_client(llm_cfg)

            if args.gsm:
                annotation, audit, is_flagged = run_single_gsm(args.gsm, config)
                annotations = [annotation]
                audits = [audit]
                flagged = [annotation] if is_flagged else []
                summary = {
                    "n_total": 1,
                    "n_accepted": 0 if is_flagged else 1,
                    "n_flagged": 1 if is_flagged else 0,
                }
            elif args.gsm_file:
                gsm_ids = _read_gsm_file(args.gsm_file)
                annotations, audits, flagged, summary = run_batch(gsm_ids, config)
            elif args.jsonl:
                (
                    annotations,
                    audits,
                    flagged,
                    summary,
                    gse_report,
                    gse_values,
                ) = run_gse_from_jsonl(args.jsonl, config, llm_client=llm_client)
            elif args.gse:
                log_gse_start_processing(args.gse)
                try:
                    (
                        annotations,
                        audits,
                        flagged,
                        summary,
                        gse_report,
                        gse_values,
                    ) = run_gse_from_accession(
                        args.gse,
                        config,
                        output_base_dir,
                        llm_client=llm_client,
                    )
                except GseSoftSkipError as exc:
                    print(
                        f"WARNING: {exc}; skipping.",
                        file=sys.stderr,
                    )
                    return
            elif args.gse_file:
                for gse_accession in gse_ids:
                    log_gse_start_processing(gse_accession)
                    try:
                        (
                            annotations,
                            audits,
                            flagged,
                            summary,
                            gse_report,
                            gse_values,
                        ) = run_gse_from_accession(
                            gse_accession,
                            config,
                            output_base_dir,
                            llm_client=llm_client,
                        )
                    except GseSoftSkipError as exc:
                        print(
                            f"WARNING: {exc}; skipping.",
                            file=sys.stderr,
                        )
                        continue

                    output_dir = _resolve_output_dir(
                        output_base_dir,
                        annotations,
                        True,
                    )
                    output_paths = None
                    if not args.dry_run:
                        suggestions = None
                        if args.emit_suggestions:
                            suggestions = build_gse_suggestions(
                                annotations, audits, config, emit_suggestions=True
                            )
                        extra_json = (
                            {"gse_consistency.json": gse_report} if gse_report else None
                        )
                        extra_jsonl = (
                            {"gse_field_values.jsonl": [gse_values]}
                            if gse_values
                            else None
                        )
                        output_paths = write_run_outputs(
                            output_dir,
                            annotations,
                            audits,
                            flagged,
                            suggestions=suggestions,
                            extra_json=extra_json,
                            extra_jsonl=extra_jsonl,
                        )
                        log_gse_outputs_written(gse_accession, output_dir)

                    _print_summary(summary, output_paths, args.dry_run)
                return
            elif args.gse_soft:
                try:
                    (
                        annotations,
                        audits,
                        flagged,
                        summary,
                        gse_report,
                        gse_values,
                    ) = run_gse_from_soft_file(
                        args.gse_soft,
                        config,
                        output_base_dir,
                        llm_client=llm_client,
                    )
                except GseSoftSkipError as exc:
                    print(
                        f"WARNING: {exc}; skipping.",
                        file=sys.stderr,
                    )
                    return
            else:
                raise ValueError("No input mode selected.")

            output_dir = _resolve_output_dir(
                output_base_dir,
                annotations,
                bool(args.jsonl or args.gse or args.gse_soft),
            )
            output_paths = None
            if not args.dry_run:
                suggestions = None
                if args.emit_suggestions:
                    suggestions = build_gse_suggestions(
                        annotations, audits, config, emit_suggestions=True
                    )
                extra_json = {"gse_consistency.json": gse_report} if gse_report else None
                extra_jsonl = (
                    {"gse_field_values.jsonl": [gse_values]} if gse_values else None
                )
                output_paths = write_run_outputs(
                    output_dir,
                    annotations,
                    audits,
                    flagged,
                    suggestions=suggestions,
                    extra_json=extra_json,
                    extra_jsonl=extra_jsonl,
                )
                for gse_accession in _collect_gse_accessions(annotations):
                    log_gse_outputs_written(gse_accession, output_dir)

            _print_summary(summary, output_paths, args.dry_run)
    except Exception as exc:
        print(f"runtime error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc


if __name__ == "__main__":
    main()
