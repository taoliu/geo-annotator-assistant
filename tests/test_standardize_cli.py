from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agent import cli as agent_cli
from agent import standardize_cli


def test_standardize_cli_defaults_resolve_paths() -> None:
    output_path, audit_path = standardize_cli.resolve_output_paths(
        "curated.jsonl",
        None,
        None,
    )
    assert output_path == "curated.jsonl.standardized.jsonl"
    assert audit_path == "curated.jsonl.standardized.jsonl.audit.jsonl"


def test_standardize_cli_short_flags_parse() -> None:
    parser = standardize_cli.build_parser()
    args = parser.parse_args(
        [
            "-i",
            "curated.jsonl",
            "-o",
            "out.jsonl",
            "-a",
            "out.audit.jsonl",
            "-c",
            "config.yaml",
            "-f",
            "disease,cell_line",
            "--canonicalize",
            "true",
        ]
    )
    assert args.input == "curated.jsonl"
    assert args.output == "out.jsonl"
    assert args.audit == "out.audit.jsonl"
    assert args.config == "config.yaml"
    assert args.fields == "disease,cell_line"
    assert args.canonicalize is True


def test_standardize_cli_help_includes_defaults_and_examples() -> None:
    help_text = standardize_cli.build_parser().format_help()
    assert "Defaults:" in help_text
    assert "output: <input>.standardized.jsonl" in help_text
    assert "audit: <output>.audit.jsonl" in help_text
    assert "canonicalize: respect config" in help_text
    assert "Examples:" in help_text
    assert "geo-gsm-annotate standardize-terms -i curated.jsonl" in help_text


def test_geo_gsm_annotate_help_lists_standardize_terms(capsys) -> None:
    with pytest.raises(SystemExit) as exc:
        agent_cli.main(["--help"])
    assert exc.value.code == 0
    output = capsys.readouterr().out
    assert "standardize-terms" in output
