"""LLM client interfaces."""

from __future__ import annotations

from typing import Protocol


class LLMClient(Protocol):
    """Minimal interface for LLM clients."""

    def generate(self, prompt: str) -> str:
        ...
