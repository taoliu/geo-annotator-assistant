"""Text post-processing helpers for LLM transports."""

from __future__ import annotations

from sympy import li


def remove_thinking(text: str, thinking_markers: list[str] = ["<think>", "</think>"]) -> str:
    finding_start = text.find(thinking_markers[0])
    finding_end = text.find(thinking_markers[1], finding_start + len(thinking_markers[0]))
    while finding_start != -1 and finding_end != -1:
        text = text[:finding_start] + text[finding_end + len(thinking_markers[1]):]
        finding_start = text.find(thinking_markers[0])
        finding_end = text.find(thinking_markers[1], finding_start + len(thinking_markers[0]))
    return text.lstrip()


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
