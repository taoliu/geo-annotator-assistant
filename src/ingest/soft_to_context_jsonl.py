"""Convert GEO SOFT files into JSONL context records."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from agent.runtime_trace import (
    log_gse_soft_download_completed,
    log_gse_soft_download_start,
    log_gse_soft_parsed,
    log_gse_using_local_soft,
)
from ingest.gse_soft_fetcher import (
    download_file_via_ftp,
    download_file_via_https,
    get_local_path,
    get_remote_path,
)
from ingest.gse_soft_parser import extract_sample_level_data
from ingest.utils import gse_dict_to_prompt

_ALLOWED_ON_MISSING = {"remote", "skip", "error"}
_ALLOWED_REMOTE_TRANSPORT = {"https", "ftp"}


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


def _download_soft(
    gse_accession: str,
    cache_dir: Path,
    remote_transport: str,
) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    remote_path = get_remote_path(gse_accession)
    if not remote_path:
        raise ValueError(f"Invalid GSE accession: {gse_accession}")
    local_path = cache_dir / f"{gse_accession}_family.soft.gz"
    if remote_transport == "https":
        download_file_via_https(remote_path, str(local_path), skip_existing_files=True)
    elif remote_transport == "ftp":
        download_file_via_ftp(remote_path, str(local_path), skip_existing_files=True)
    else:
        raise ValueError(
            "Invalid geo_soft_remote_transport. "
            f"Expected one of {sorted(_ALLOWED_REMOTE_TRANSPORT)}, got {remote_transport!r}."
        )
    if not local_path.is_file():
        raise FileNotFoundError(
            f"SOFT file not found for {gse_accession} after download attempt: {local_path}"
        )
    return local_path


def _context_basename(source: Path) -> str:
    name = source.name
    if name.endswith(".gz"):
        name = name[:-3]
    if name.endswith(".soft"):
        name = name[:-5]
    return name or source.stem


class LocalSoftMissingError(FileNotFoundError):
    def __init__(self, gse_accession: str, path: str) -> None:
        super().__init__(f"GEO SOFT file not found for {gse_accession} at {path}")
        self.gse_accession = gse_accession
        self.path = path


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
    geo_soft_local_dir: str | Path | None = None,
    geo_soft_on_missing: str = "remote",
    geo_soft_remote_transport: str = "https",
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
    if geo_soft_on_missing not in _ALLOWED_ON_MISSING:
        raise ValueError(
            "Invalid geo_soft_on_missing. "
            f"Expected one of {sorted(_ALLOWED_ON_MISSING)}, got {geo_soft_on_missing!r}."
        )
    if geo_soft_remote_transport not in _ALLOWED_REMOTE_TRANSPORT:
        raise ValueError(
            "Invalid geo_soft_remote_transport. "
            f"Expected one of {sorted(_ALLOWED_REMOTE_TRANSPORT)}, got {geo_soft_remote_transport!r}."
        )

    if geo_soft_local_dir:
        print(
            f"INFO: {gse_accession}: resolving SOFT (local-first)",
            file=sys.stderr,
        )
        local_path = get_local_path(gse_accession, str(geo_soft_local_dir))
        if not local_path:
            raise ValueError(f"Invalid GSE accession: {gse_accession}")
        soft_file = Path(local_path)
        if soft_file.is_file():
            print(
                f"INFO: {gse_accession}: using local SOFT at {soft_file}",
                file=sys.stderr,
            )
            log_gse_using_local_soft(gse_accession)
        elif geo_soft_on_missing == "skip":
            print(
                f"WARNING: {gse_accession}: local SOFT missing at {soft_file}; skipping (geo_soft_on_missing=skip)",
                file=sys.stderr,
            )
            raise LocalSoftMissingError(gse_accession, str(soft_file))
        elif geo_soft_on_missing == "error":
            print(
                f"ERROR: {gse_accession}: local SOFT missing at {soft_file}; aborting (geo_soft_on_missing=error)",
                file=sys.stderr,
            )
            raise FileNotFoundError(
                f"Local SOFT file not found for {gse_accession} at {soft_file}"
            )
        else:
            print(
                f"WARNING: {gse_accession}: local SOFT missing at {soft_file}; downloading via {geo_soft_remote_transport}",
                file=sys.stderr,
            )
            log_gse_soft_download_start(gse_accession, geo_soft_remote_transport)
            soft_file = _download_soft(
                gse_accession,
                soft_file.parent,
                geo_soft_remote_transport,
            )
            print(
                f"INFO: {gse_accession}: downloaded SOFT to {soft_file}",
                file=sys.stderr,
            )
            log_gse_soft_download_completed(gse_accession)
        jsonl_path = context_dir / f"{gse_accession}_contexts.jsonl"
        if jsonl_path.is_file():
            return str(jsonl_path)
        result = _write_context_jsonl(soft_file, jsonl_path)
        log_gse_soft_parsed(gse_accession)
        return result

    print(
        f"INFO: {gse_accession}: resolving SOFT (remote-only)",
        file=sys.stderr,
    )
    soft_file = None
    if soft_cache_dir:
        soft_file = _find_cached_soft(gse_accession, Path(soft_cache_dir))
        if soft_file is not None:
            print(
                f"INFO: {gse_accession}: using cached SOFT at {soft_file}",
                file=sys.stderr,
            )

    local_cache_dir = work_dir / "soft_cache"
    if soft_file is None:
        soft_file = _find_cached_soft(gse_accession, local_cache_dir)
        if soft_file is not None:
            print(
                f"INFO: {gse_accession}: using cached SOFT at {soft_file}",
                file=sys.stderr,
            )
    if soft_file is None:
        print(
            f"INFO: {gse_accession}: downloading SOFT via {geo_soft_remote_transport}",
            file=sys.stderr,
        )
        log_gse_soft_download_start(gse_accession, geo_soft_remote_transport)
        soft_file = _download_soft(
            gse_accession,
            local_cache_dir,
            geo_soft_remote_transport,
        )
        print(
            f"INFO: {gse_accession}: downloaded SOFT to {soft_file}",
            file=sys.stderr,
        )
        log_gse_soft_download_completed(gse_accession)

    jsonl_path = context_dir / f"{gse_accession}_contexts.jsonl"
    if jsonl_path.is_file():
        return str(jsonl_path)
    result = _write_context_jsonl(soft_file, jsonl_path)
    log_gse_soft_parsed(gse_accession)
    return result
