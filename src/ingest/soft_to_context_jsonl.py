"""Convert GEO SOFT files into JSONL context records."""

from __future__ import annotations

import json
from pathlib import Path

from ingest.gse_soft_fetcher import download_file_via_https, get_remote_path
from ingest.gse_soft_parser import extract_sample_level_data
from ingest.utils import gse_dict_to_prompt


def _soft_cache_candidates(gse_accession: str) -> list[str]:
    return [
        f"{gse_accession}_family.soft.gz",
        f"{gse_accession}_family.soft",
        f"{gse_accession}.soft.gz",
        f"{gse_accession}.soft",
    ]


def _find_cached_soft(gse_accession: str, cache_dir: Path) -> Path | None:
    if not cache_dir.exists():
        return None
    for candidate in _soft_cache_candidates(gse_accession):
        path = cache_dir / candidate
        if path.is_file():
            return path
    return None


def _download_soft(gse_accession: str, cache_dir: Path) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    remote_path = get_remote_path(gse_accession)
    if not remote_path:
        raise ValueError(f"Invalid GSE accession: {gse_accession}")
    local_path = cache_dir / f"{gse_accession}_family.soft.gz"
    download_file_via_https(remote_path, str(local_path), skip_existing_files=True)
    if not local_path.is_file():
        raise FileNotFoundError(
            f"SOFT file not found after download attempt: {local_path}"
        )
    return local_path


def _context_basename(source: Path) -> str:
    name = source.name
    if name.endswith(".gz"):
        name = name[:-3]
    if name.endswith(".soft"):
        name = name[:-5]
    return name or source.stem


def _write_context_jsonl(soft_path: Path, output_path: Path) -> str:
    gse_dict = extract_sample_level_data(str(soft_path))
    if not gse_dict:
        raise ValueError(f"No sample data extracted from {soft_path}")
    records = gse_dict_to_prompt(gse_dict)
    if not records:
        raise ValueError(f"No context records built from {soft_path}")
    with output_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=True))
            handle.write("\n")
    return str(output_path)


def soft_to_context_jsonl(
    *,
    gse_accession: str | None = None,
    soft_path: str | None = None,
    work_dir: str | Path,
    soft_cache_dir: str | Path | None = None,
) -> str:
    if (gse_accession is None) == (soft_path is None):
        raise ValueError("Provide exactly one of gse_accession or soft_path.")

    work_dir = Path(work_dir)
    context_dir = work_dir / "context_cache"
    context_dir.mkdir(parents=True, exist_ok=True)

    if soft_path is not None:
        soft_file = Path(soft_path)
        if not soft_file.is_file():
            raise ValueError(f"SOFT file not found: {soft_path}")
        jsonl_path = context_dir / f"{_context_basename(soft_file)}_contexts.jsonl"
        if jsonl_path.is_file():
            return str(jsonl_path)
        return _write_context_jsonl(soft_file, jsonl_path)

    gse_accession = gse_accession or ""
    if not gse_accession:
        raise ValueError("gse_accession is required.")

    soft_file = None
    if soft_cache_dir:
        soft_file = _find_cached_soft(gse_accession, Path(soft_cache_dir))

    local_cache_dir = work_dir / "soft_cache"
    if soft_file is None:
        soft_file = _find_cached_soft(gse_accession, local_cache_dir)
    if soft_file is None:
        soft_file = _download_soft(gse_accession, local_cache_dir)

    jsonl_path = context_dir / f"{gse_accession}_contexts.jsonl"
    if jsonl_path.is_file():
        return str(jsonl_path)
    return _write_context_jsonl(soft_file, jsonl_path)
