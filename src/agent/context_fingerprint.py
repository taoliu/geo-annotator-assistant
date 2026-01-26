"""Context fingerprinting utilities for GEO GSM records."""

from __future__ import annotations

import hashlib
import re

_SAMPLE_ID_PREFIX = "Sample ID:"
_SAMPLE_FILENAME_PREFIX = "Sample Filename:"
_SAMPLE_TITLE_PREFIX = "Sample Title:"
_SAMPLE_TITLE_PATTERN = re.compile(r"^(Sample Title:\s*)(.*)$")
_ID_KEYWORD_PATTERN = re.compile(
    r"(^|[^A-Za-z0-9])"
    r"(patient|donor|subject)([\s_-]+)([A-Za-z0-9-]*\d+[A-Za-z0-9-]*)",
    re.IGNORECASE,
)
_REPLICATE_MARKER_PATTERN = re.compile(
    r"\b(techrep(?:licate)?|biorep(?:licate)?|rep(?:licate)?)"
    r"(?:[\s_-]*)(\d+)\b",
    re.IGNORECASE,
)
_REPLICATE_INDEX_PATTERN = re.compile(
    r"\b(sample|animal)(?:[\s_-]*)(\d+)\b",
    re.IGNORECASE,
)
_TRAILING_HASH_PATTERN = re.compile(r"(#)(\d+)(\s*)$", re.IGNORECASE)


def _normalize_sample_title(title: str) -> str:
    def _replace_id(match: re.Match) -> str:
        prefix = match.group(1)
        keyword = match.group(2)
        separator = match.group(3)
        return f"{prefix}{keyword}{separator}<ID>"

    def _replace_replicate_marker(match: re.Match) -> str:
        keyword = match.group(1).lower()
        number = match.group(2)
        if keyword.startswith("bio"):
            label = "biorep"
        elif keyword.startswith("tech"):
            label = "techrep"
        else:
            label = "replicate"
        return f"{label} <N>"

    def _replace_replicate_index(match: re.Match) -> str:
        keyword = match.group(1).lower()
        return f"{keyword} <N>"

    normalized = _ID_KEYWORD_PATTERN.sub(_replace_id, title)
    normalized = _REPLICATE_MARKER_PATTERN.sub(_replace_replicate_marker, normalized)
    normalized = _REPLICATE_INDEX_PATTERN.sub(_replace_replicate_index, normalized)
    normalized = _TRAILING_HASH_PATTERN.sub(r"#<N>\3", normalized)
    return normalized


def normalize_context_text(context_text: str) -> str:
    """Normalize context text for deterministic caching.

    Rules:
    - Drop the line starting with "Sample ID:".
    - Normalize anchored identifier/replicate patterns in the "Sample Title:" line.
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
