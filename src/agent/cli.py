"""CLI entrypoint for geo-gsm-annotator-agent."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from agent.config import load_config
from agent.run_batch import run_batch
from agent.run_single import run_single_gsm
from agent.writer import write_run_outputs


class _ArgumentParser(argparse.ArgumentParser):
    """ArgumentParser that exits with code 1 on usage errors."""

    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        self.exit(1, f"error: {message}\n")


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


def _build_parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(description="Run the GEO GSM annotator agent.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--gsm", help="Single GSM identifier to process.")
    group.add_argument("--gsm-file", help="Path to a file containing GSM identifiers.")
    parser.add_argument("--output-dir", default="outputs", help="Directory for outputs.")
    parser.add_argument("--config", required=True, help="Path to YAML config file.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run the pipeline but skip writing output files.",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)

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
        else:
            gsm_ids = _read_gsm_file(args.gsm_file)
            annotations, audits, flagged, summary = run_batch(gsm_ids, config)

        output_paths = None
        if not args.dry_run:
            output_paths = write_run_outputs(
                args.output_dir, annotations, audits, flagged
            )

        _print_summary(summary, output_paths, args.dry_run)
    except Exception as exc:
        print(f"runtime error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc


if __name__ == "__main__":
    main()
