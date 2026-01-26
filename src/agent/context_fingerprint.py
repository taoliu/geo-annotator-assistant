"""Context fingerprinting utilities for GEO GSM records."""

from __future__ import annotations

import hashlib
import re

_SAMPLE_ID_PREFIX = "Sample ID:"
_SAMPLE_FILENAME_PREFIX = "Sample Filename:"
_SAMPLE_TITLE_PREFIX = "Sample Title:"
_SAMPLE_TITLE_PATTERN = re.compile(r"^(Sample Title:\s*)(.*)$")
_NUMERIC_SUFFIX_PATTERN = re.compile(r"(\b[^\s]+?)([_-])(\d+)\b")
_REPLICATE_PATTERN = re.compile(r"\b(rep(?:licate)?)(?:[\s_-]*)(\d+)\b", re.IGNORECASE)


def _normalize_sample_title(title: str) -> str:
    normalized = _REPLICATE_PATTERN.sub(r"replicate <N>", title)
    return _NUMERIC_SUFFIX_PATTERN.sub(r"\1\2<N>", normalized)


def normalize_context_text(context_text: str) -> str:
    """Normalize context text for deterministic caching.

    Rules:
    - Drop the line starting with "Sample ID:".
    - Normalize numeric-only suffixes in the "Sample Title:" line.
    - Leave all other lines unchanged.
    """
    if not context_text:
        return ""

    normalized_lines: list[str] = []
    for line in context_text.splitlines(keepends=True):
        line_end = ""
        stripped = line
        if line.endswith("\r\n"):
            line_end = "\r\n"
            stripped = line[:-2]
        elif line.endswith("\n") or line.endswith("\r"):
            line_end = line[-1]
            stripped = line[:-1]

        if stripped.startswith(_SAMPLE_ID_PREFIX):
            continue
        if stripped.startswith(_SAMPLE_FILENAME_PREFIX):
            continue

        title_match = _SAMPLE_TITLE_PATTERN.match(stripped)
        if title_match:
            prefix, title = title_match.groups()
            normalized_title = _normalize_sample_title(title)
            normalized_lines.append(f"{prefix}{normalized_title}{line_end}")
            continue

        normalized_lines.append(stripped + line_end)

    return "".join(normalized_lines)


def compute_context_fingerprint(context_text: str) -> str:
    """Return a stable SHA-256 fingerprint for normalized context text."""
    normalized = normalize_context_text(context_text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
