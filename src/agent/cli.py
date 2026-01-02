"""CLI entrypoint for geo-gsm-annotator-agent."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from agent.config import load_config
from agent.prompts import load_prompts


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


def _get_nested(config: dict[str, Any], *keys: str) -> Any:
    current: Any = config
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _print_summary(gsm_ids: list[str], config: dict[str, Any], prompts: dict[str, str]) -> None:
    print(f"GSM count: {len(gsm_ids)}")

    prompt_version = _get_nested(config, "versions", "prompt_version")
    if prompt_version is not None:
        print(f"Prompt version: {prompt_version}")

    validator_version = _get_nested(config, "versions", "validator_version")
    if validator_version is not None:
        print(f"Validator version: {validator_version}")

    rag_persist_path = _get_nested(config, "rag", "persist_path")
    if rag_persist_path is None:
        rag_persist_path = "(missing)"
    print(f"RAG persist path: {rag_persist_path}")

    rag_collections = _get_nested(config, "rag", "collections")
    if isinstance(rag_collections, dict):
        collection_keys = sorted(rag_collections.keys())
    else:
        collection_keys = []
    collections_label = ", ".join(collection_keys) if collection_keys else "(none)"
    print(f"RAG collections: {collections_label}")

    prompt_files = ", ".join(sorted(prompts.keys()))
    print(f"Loaded prompts: {prompt_files}")


def _build_parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(description="Run the GEO GSM annotator agent.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--gsm", help="Single GSM identifier to process.")
    group.add_argument("--gsm-file", help="Path to a file containing GSM identifiers.")
    parser.add_argument("--output-dir", default="outputs", help="Directory for outputs.")
    parser.add_argument("--config", required=True, help="Path to YAML config file.")
    parser.add_argument("--dry-run", action="store_true", help="Load config/prompts only.")
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        if args.gsm:
            gsm_ids = [args.gsm]
        else:
            gsm_ids = _read_gsm_file(args.gsm_file)

        config = load_config(args.config)

        prompt_dir = Path.cwd() / "prompts"
        prompts = load_prompts(str(prompt_dir))

        _print_summary(gsm_ids, config, prompts)

        if not args.dry_run:
            print("Pipeline stub: no processing performed.")
    except Exception as exc:
        print(f"runtime error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc


if __name__ == "__main__":
    main()
