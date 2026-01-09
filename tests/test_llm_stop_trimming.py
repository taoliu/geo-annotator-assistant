from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from llm.base import LLMRequest
from llm.local_transformers import LocalTransformersClient
from llm.openai_http import OpenAIHttpClient
from llm.text_postprocess import apply_stop


def test_apply_stop_no_list_returns_text() -> None:
    assert apply_stop("hello", None) == "hello"
    assert apply_stop("hello", []) == "hello"


def test_apply_stop_trims_at_first_match() -> None:
    text = "alpha<|eot_id|>beta"
    assert apply_stop(text, ["<|eot_id|>"]) == "alpha"


def test_apply_stop_trims_at_earliest_stop() -> None:
    text = "alphaENDbetaSTOPgamma"
    assert apply_stop(text, ["STOP", "END"]) == "alpha"


def test_local_transformers_stop_helper_matches_shared() -> None:
    text = "alpha<|eot_id|>beta"
    expected = apply_stop(text, ["<|eot_id|>"])
    assert LocalTransformersClient._apply_stop(text, ["<|eot_id|>"]) == expected


def test_openai_http_applies_stop(monkeypatch: pytest.MonkeyPatch) -> None:
    client = OpenAIHttpClient(
        {"openai_http": {"base_url": "http://example.com", "model": "test-model"}}
    )

    def _fake_post(url: str, payload: dict, headers: dict, **_kwargs):
        return {"choices": [{"message": {"content": "alpha<|eot_id|>beta"}}]}, {
            "retry_count": 0,
            "backoff_s": [],
            "timeout_s": 30.0,
            "last_http_status": 200,
            "latency_ms": 1,
        }

    monkeypatch.setattr("llm.openai_http.post_json_with_retries", _fake_post)

    request = LLMRequest(
        prompt="hello",
        system=None,
        model=None,
        max_tokens=None,
        temperature=None,
        top_p=None,
        stop=["<|eot_id|>"],
        seed=None,
        request_id="req-1",
        tags={"stage": "label"},
    )
    result = client.generate(request)
    assert result.text == "alpha"
