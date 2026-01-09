from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from llm.base import LLMRequest
from llm.http_utils import LLMTransportError, post_json_with_retries
from llm.openai_http import OpenAIHttpClient


def _build_request() -> LLMRequest:
    return LLMRequest(
        prompt="hello",
        system=None,
        model=None,
        max_tokens=None,
        temperature=None,
        top_p=None,
        stop=None,
        seed=None,
        request_id="req-1",
        tags={"stage": "label"},
    )


def test_retryable_status_retries_once() -> None:
    responses = [(502, None), (200, {"ok": True})]
    calls: list[tuple[int, dict | None]] = []
    slept: list[float] = []

    def _post(url: str, payload_text: str, headers: dict, timeout_s: float):
        status, data = responses.pop(0)
        calls.append((status, data))
        return status, data

    def _sleep(seconds: float) -> None:
        slept.append(seconds)

    data, meta = post_json_with_retries(
        "http://example.com",
        {"payload": "x"},
        {"Content-Type": "application/json"},
        timeout_s=5.0,
        max_retries=2,
        request_id="req-1",
        endpoint="chat_completions",
        post_func=_post,
        sleep_fn=_sleep,
    )

    assert data == {"ok": True}
    assert len(calls) == 2
    assert meta["retry_count"] == 1
    assert meta["backoff_s"] == [0.5]
    assert slept == [0.5]


def test_429_retries() -> None:
    responses = [(429, None), (200, {"ok": True})]
    slept: list[float] = []

    def _post(url: str, payload_text: str, headers: dict, timeout_s: float):
        return responses.pop(0)

    def _sleep(seconds: float) -> None:
        slept.append(seconds)

    data, meta = post_json_with_retries(
        "http://example.com",
        {"payload": "x"},
        {"Content-Type": "application/json"},
        timeout_s=5.0,
        max_retries=2,
        request_id="req-1",
        endpoint="chat_completions",
        post_func=_post,
        sleep_fn=_sleep,
    )

    assert data == {"ok": True}
    assert meta["retry_count"] == 1
    assert meta["backoff_s"] == [0.5]
    assert slept == [0.5]


def test_non_retryable_4xx_raises() -> None:
    calls = 0

    def _post(url: str, payload_text: str, headers: dict, timeout_s: float):
        nonlocal calls
        calls += 1
        return 400, None

    with pytest.raises(LLMTransportError) as exc_info:
        post_json_with_retries(
            "http://example.com",
            {"payload": "x"},
            {"Content-Type": "application/json"},
            timeout_s=5.0,
            max_retries=2,
            request_id="req-1",
            endpoint="chat_completions",
            post_func=_post,
        )

    assert calls == 1
    assert exc_info.value.transport_meta["retry_count"] == 0
    assert exc_info.value.transport_meta["backoff_s"] == []
    assert exc_info.value.transport_meta["last_http_status"] == 400


def test_timeout_is_retryable() -> None:
    calls = 0
    slept: list[float] = []

    def _post(url: str, payload_text: str, headers: dict, timeout_s: float):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise TimeoutError("timed out")
        return 200, {"ok": True}

    def _sleep(seconds: float) -> None:
        slept.append(seconds)

    data, meta = post_json_with_retries(
        "http://example.com",
        {"payload": "x"},
        {"Content-Type": "application/json"},
        timeout_s=7.5,
        max_retries=2,
        request_id="req-1",
        endpoint="chat_completions",
        post_func=_post,
        sleep_fn=_sleep,
    )

    assert data == {"ok": True}
    assert meta["retry_count"] == 1
    assert meta["backoff_s"] == [0.5]
    assert meta["timeout_s"] == 7.5
    assert slept == [0.5]


def test_request_fingerprint_unchanged_by_retry_meta(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = OpenAIHttpClient(
        {
            "openai_http": {
                "base_url": "http://example.com",
                "model": "test-model",
            }
        }
    )

    request = _build_request()

    def _fake_post_retry(url: str, payload: dict, headers: dict, **_kwargs):
        return {"choices": [{"message": {"content": "ok"}}]}, {
            "retry_count": 1,
            "backoff_s": [0.5],
            "timeout_s": 30.0,
            "last_http_status": 200,
            "latency_ms": 5,
        }

    def _fake_post_no_retry(url: str, payload: dict, headers: dict, **_kwargs):
        return {"choices": [{"message": {"content": "ok"}}]}, {
            "retry_count": 0,
            "backoff_s": [],
            "timeout_s": 30.0,
            "last_http_status": 200,
            "latency_ms": 2,
        }

    monkeypatch.setattr("llm.openai_http.post_json_with_retries", _fake_post_retry)
    fp_retry = client.generate(request).request_fingerprint

    monkeypatch.setattr("llm.openai_http.post_json_with_retries", _fake_post_no_retry)
    fp_no_retry = client.generate(request).request_fingerprint

    assert fp_retry == fp_no_retry
