"""LLM client interfaces."""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from typing import Any, Protocol


@dataclass(frozen=True)
class LLMRequest:
    prompt: str
    system: str | None
    model: str | None
    max_tokens: int | None
    temperature: float | None
    top_p: float | None
    stop: list[str] | None
    seed: int | None
    request_id: str
    tags: dict[str, str] = field(default_factory=dict)

    def fingerprint_payload(self) -> dict[str, Any]:
        return {
            "prompt": self.prompt,
            "system": self.system,
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "stop": self.stop,
            "seed": self.seed,
            "tags": self.tags,
        }


@dataclass(frozen=True)
class LLMResult:
    text: str
    request_id: str
    usage: dict[str, Any] | None
    transport_meta: dict[str, Any]
    request_fingerprint: str


def compute_request_fingerprint(request: LLMRequest) -> str:
    payload = request.fingerprint_payload()
    serialized = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class LLMClient(Protocol):
    """Minimal interface for LLM clients."""

    def generate(self, request: LLMRequest) -> LLMResult:
        ...
