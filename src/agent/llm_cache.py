"""In-memory LLM cache keyed by deterministic context fingerprints."""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from typing import Any, Dict, Optional

from llm.base import LLMRequest


@dataclass
class LLMCacheEntry:
    raw_outputs: list[str]
    parsed_outputs: list[Dict[str, Any]]
    format_errors: list[str]
    repair_history: list[Dict[str, Any]]


@dataclass
class LLMCache:
    entries: Dict[str, LLMCacheEntry] = field(default_factory=dict)
    hits: int = 0
    misses: int = 0

    def get(self, key: str) -> Optional[LLMCacheEntry]:
        entry = self.entries.get(key)
        if entry is None:
            self.misses += 1
        else:
            self.hits += 1
        return entry

    def set(self, key: str, entry: LLMCacheEntry) -> None:
        self.entries[key] = entry


def build_llm_cache_key(
    *,
    gse_accession: str,
    context_fingerprint: str,
    request: LLMRequest,
    versions: Dict[str, str],
    prompt_name: str,
) -> str:
    payload = {
        "gse_accession": gse_accession,
        "context_fingerprint": context_fingerprint,
        "prompt_name": prompt_name,
        "versions": versions,
        "model": request.model,
        "system": request.system,
        "max_tokens": request.max_tokens,
        "temperature": request.temperature,
        "top_p": request.top_p,
        "stop": request.stop,
        "seed": request.seed,
        "tags": request.tags,
    }
    serialized = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
