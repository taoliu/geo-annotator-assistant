from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from llm.base import LLMRequest
from llm.openai_http import OpenAIHttpClient


def _build_request(**overrides) -> LLMRequest:
    data = {
        "prompt": "hello",
        "system": None,
        "model": None,
        "max_tokens": None,
        "temperature": None,
        "top_p": None,
        "stop": None,
        "seed": None,
        "request_id": "req-1",
        "tags": {"stage": "label"},
    }
    data.update(overrides)
    return LLMRequest(**data)


def _make_client() -> OpenAIHttpClient:
    return OpenAIHttpClient(
        {
            "openai_http": {
                "base_url": "http://example.com",
                "model": "test-model",
                "default_max_tokens": 123,
            }
        }
    )


def test_payload_defaults_include_deterministic_params(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _make_client()
    captured: dict[str, object] = {}

    def _fake_post(url: str, payload: dict, headers: dict):
        captured["url"] = url
        captured["payload"] = payload
        captured["headers"] = headers
        return 200, {"choices": [{"message": {"content": "ok"}}]}

    monkeypatch.setattr(client, "_post_json", _fake_post)

    client.generate(_build_request())

    payload = captured["payload"]
    assert isinstance(payload, dict)
    assert payload["temperature"] == 0.0
    assert payload["top_p"] == 1.0
    assert payload["model"] == "test-model"
    assert payload["max_tokens"] == 123


def test_response_parsing_extracts_text(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _make_client()

    def _fake_post(url: str, payload: dict, headers: dict):
        return 200, {"choices": [{"message": {"content": "hello world"}}]}

    monkeypatch.setattr(client, "_post_json", _fake_post)

    result = client.generate(_build_request())

    assert result.text == "hello world"


def test_request_fingerprint_determinism(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _make_client()

    def _fake_post(url: str, payload: dict, headers: dict):
        return 200, {"choices": [{"message": {"content": "ok"}}]}

    monkeypatch.setattr(client, "_post_json", _fake_post)

    base_request = _build_request()
    base_fp = client.generate(base_request).request_fingerprint

    assert client.generate(_build_request()).request_fingerprint == base_fp

    assert (
        client.generate(_build_request(prompt="hello 2")).request_fingerprint
        != base_fp
    )
    assert (
        client.generate(_build_request(system="system")).request_fingerprint
        != base_fp
    )
    assert (
        client.generate(_build_request(model="alternate-model")).request_fingerprint
        != base_fp
    )
    assert (
        client.generate(_build_request(temperature=0.5)).request_fingerprint
        != base_fp
    )
    assert (
        client.generate(_build_request(top_p=0.9)).request_fingerprint
        != base_fp
    )
    assert (
        client.generate(_build_request(max_tokens=5)).request_fingerprint
        != base_fp
    )
    assert (
        client.generate(_build_request(stop=["END"])).request_fingerprint
        != base_fp
    )
    assert (
        client.generate(_build_request(seed=42)).request_fingerprint
        != base_fp
    )
