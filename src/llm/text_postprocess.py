"""Text post-processing helpers for LLM transports."""

from __future__ import annotations


def apply_stop(text: str, stop_list: list[str] | None) -> str:
    if not stop_list:
        return text
    earliest = None
    for stop in stop_list:
        idx = text.find(stop)
        if idx != -1 and (earliest is None or idx < earliest):
            earliest = idx
    if earliest is None:
        return text
    return text[:earliest]
