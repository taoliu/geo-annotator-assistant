from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from llm.base import LLMRequest
from llm.factory import create_llm_client


def _build_request(prompt: str, request_id: str = "req-1") -> LLMRequest:
    return LLMRequest(
        prompt=prompt,
        system=None,
        model=None,
        max_tokens=None,
        temperature=None,
        top_p=None,
        stop=None,
        seed=None,
        request_id=request_id,
        tags={"stage": "label"},
    )


def test_factory_selects_local_transformers(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeLocalTransformersClient:
        def __init__(self, cfg: dict) -> None:
            self._device = cfg.get("device", "cpu")

    fake_module = types.SimpleNamespace(LocalTransformersClient=FakeLocalTransformersClient)
    monkeypatch.setitem(sys.modules, "llm.local_transformers", fake_module)

    client = create_llm_client(
        {"transport": "local_transformers", "model_path": "fake-model", "device": "cpu"}
    )

    assert isinstance(client, FakeLocalTransformersClient)


def test_factory_creates_openai_http_client() -> None:
    client = create_llm_client(
        {
            "transport": "openai_http",
            "openai_http": {
                "base_url": "http://example.com",
                "model": "test-model",
            },
        }
    )

    assert client.__class__.__name__ == "OpenAIHttpClient"


def test_factory_creates_llama_cpp_http_stub() -> None:
    client = create_llm_client({"transport": "llama_cpp_http"})

    assert client.__class__.__name__ == "LlamaCppHttpClient"
    with pytest.raises(NotImplementedError):
        client.generate(_build_request("hello"))


def test_request_fingerprint_is_deterministic() -> None:
    client = create_llm_client({"transport": "stub"})

    request_a = _build_request("hello")
    request_b = _build_request("hello")

    result_a = client.generate(request_a)
    result_b = client.generate(request_b)

    assert result_a.request_fingerprint == result_b.request_fingerprint
