"""OpenAI-style HTTP transport (stub)."""

from __future__ import annotations

from typing import Any, Dict, Optional

from llm.base import LLMRequest, LLMResult


class OpenAIHttpClient:
    """Placeholder for OpenAI-compatible HTTP transport."""

    def __init__(self, cfg: Optional[Dict[str, Any]] = None) -> None:
        self._cfg = cfg or {}

    def generate(self, request: LLMRequest) -> LLMResult:
        raise NotImplementedError("openai_http transport not implemented")
