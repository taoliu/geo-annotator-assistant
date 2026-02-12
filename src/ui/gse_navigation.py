"""Helpers for deterministic active-GSE navigation state."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal


def ensure_active_gse(value: object, options: Sequence[str]) -> str:
    if not options:
        raise ValueError("GSE options must be non-empty.")
    if isinstance(value, str) and value in options:
        return value
    return options[0]


def step_active_gse(
    active_gse: str,
    options: Sequence[str],
    direction: Literal["prev", "next"],
) -> str:
    if active_gse not in options:
        raise ValueError(f"Active GSE '{active_gse}' not present in options.")
    index = options.index(active_gse)
    if direction == "prev":
        return options[index - 1] if index > 0 else active_gse
    if direction == "next":
        return options[index + 1] if index < (len(options) - 1) else active_gse
    raise ValueError(f"Unsupported direction: {direction}")


__all__ = ["ensure_active_gse", "step_active_gse"]
