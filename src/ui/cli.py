"""CLI entrypoint for the read-only Streamlit UI."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from ui.paths import resolve_input_paths


class _ArgumentParser(argparse.ArgumentParser):
    """ArgumentParser that exits with code 1 on usage errors."""

    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        self.exit(1, f"error: {message}\n")


def _build_parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(description="Launch the GEO GSM curator UI.")
    parser.add_argument(
        "--input-dir",
        required=True,
        help="Directory containing curation.jsonl and evidence.jsonl",
    )
    return parser


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    return _build_parser().parse_args(argv)


def _streamlit_script_path() -> Path:
    return Path(__file__).resolve().parent / "app_streamlit.py"


def _launch_streamlit(input_dir: str) -> None:
    script_path = _streamlit_script_path()
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        os.fspath(script_path),
        "--",
        "--input-dir",
        input_dir,
    ]
    env = os.environ.copy()
    env["GEO_GSM_UI_INPUT_DIR"] = input_dir
    subprocess.run(cmd, check=True, env=env)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    try:
        resolve_input_paths(args.input_dir)
        _launch_streamlit(args.input_dir)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc


if __name__ == "__main__":
    main()
