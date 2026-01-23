"""OpenAI-style HTTP transport."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Optional
from urllib.parse import urlparse

from llm.base import LLMRequest, LLMResult
from llm.http_utils import LLMTransportError, post_json_with_retries
from llm.text_postprocess import apply_stop, remove_thinking


class OpenAIHttpClient:
    """OpenAI-compatible HTTP transport."""

    def __init__(self, cfg: Optional[Dict[str, Any]] = None) -> None:
        self._cfg = cfg or {}
        openai_cfg = (
            self._cfg.get("openai_http")
            if isinstance(self._cfg.get("openai_http"), dict)
            else {}
        )
        self._base_url = str(openai_cfg.get("base_url") or "").strip()
        self._api_key = openai_cfg.get("api_key")
        self._model = openai_cfg.get("model")
        self._endpoint = openai_cfg.get("endpoint", "chat_completions")
        timeout_value = openai_cfg.get("timeout_s")
        self._timeout_s = float(timeout_value) if timeout_value is not None else 30.0
        max_tokens_value = openai_cfg.get("default_max_tokens")
        self._default_max_tokens = (
            int(max_tokens_value) if max_tokens_value is not None else 256
        )
        max_retries_value = openai_cfg.get("max_retries")
        self._max_retries = (
            int(max_retries_value) if max_retries_value is not None else 2
        )
        self._normalized_base_url = self._normalize_base_url(self._base_url)
        stop = self._cfg.get("stop") or []
        if isinstance(stop, str):
            stop = [stop]
        self._stop = [str(item) for item in stop if str(item)]

    @staticmethod
    def _normalize_base_url(base_url: str) -> str:
        value = base_url.strip().rstrip("/")
        if not value:
            return value
        parsed = urlparse(value)
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}"
        return value

    @staticmethod
    def _fingerprint_hash(payload: dict[str, Any]) -> str:
        serialized = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        )
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def _effective_model(self, request: LLMRequest) -> str | None:
        return request.model or self._model

    def _effective_params(self, request: LLMRequest) -> dict[str, Any]:
        temperature = 0.0 if request.temperature is None else float(request.temperature)
        top_p = 1.0 if request.top_p is None else float(request.top_p)
        max_tokens = (
            int(request.max_tokens)
            if request.max_tokens is not None
            else self._default_max_tokens
        )
        return {
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
        }

    def _endpoint_path(self) -> str:
        if self._endpoint == "chat_completions":
            return "/v1/chat/completions"
        if self._endpoint == "responses":
            return "/v1/responses"
        raise ValueError(f"Unsupported openai_http endpoint: {self._endpoint}")

    def _build_headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    def _build_payload(self, request: LLMRequest) -> dict[str, Any]:
        model = self._effective_model(request)
        if not model:
            raise ValueError(
                "llm.openai_http.model is required for openai_http transport"
            )

        params = self._effective_params(request)
        if self._endpoint == "chat_completions":
            messages = []
            if request.system is not None:
                messages.append({"role": "system", "content": request.system})
            messages.append({"role": "user", "content": request.prompt})
            payload: dict[str, Any] = {
                "model": model,
                "messages": messages,
                "temperature": params["temperature"],
                "top_p": params["top_p"],
                "max_tokens": params["max_tokens"],
            }
            if request.stop:
                payload["stop"] = request.stop
            if request.seed is not None:
                payload["seed"] = int(request.seed)
            return payload

        raise ValueError(f"Unsupported openai_http endpoint: {self._endpoint}")

    def _parse_text(self, data: dict[str, Any]) -> str:
        if self._endpoint == "chat_completions":
            try:
                choices = data["choices"]
                return choices[0]["message"]["content"]
            except Exception as exc:
                raise RuntimeError(
                    "Unexpected response schema from openai_http chat_completions"
                ) from exc
        raise RuntimeError(f"Unsupported openai_http endpoint: {self._endpoint}")

    def _build_fingerprint(self, request: LLMRequest) -> str:
        model = self._effective_model(request)
        params = self._effective_params(request)
        payload = request.fingerprint_payload()
        payload.update(
            {
                "model": model,
                "max_tokens": params["max_tokens"],
                "temperature": params["temperature"],
                "top_p": params["top_p"],
                "endpoint": self._endpoint,
                "base_url": self._normalized_base_url or self._base_url,
            }
        )
        return self._fingerprint_hash(payload)

    def generate(self, request: LLMRequest) -> LLMResult:
        if not self._base_url:
            raise ValueError(
                "llm.openai_http.base_url is required for openai_http transport"
            )

        url = f"{self._base_url.rstrip('/')}{self._endpoint_path()}"
        payload = self._build_payload(request)
        headers = self._build_headers()
        try:
            data, transport_meta = post_json_with_retries(
                url,
                payload,
                headers,
                timeout_s=self._timeout_s,
                max_retries=self._max_retries,
                request_id=request.request_id,
                endpoint=self._endpoint,
            )
        except LLMTransportError as exc:
            exc.transport_meta.update(
                {
                    "provider": "openai_http",
                    "base_url": self._normalized_base_url or self._base_url,
                    "model": self._effective_model(request),
                    "endpoint": self._endpoint,
                }
            )
            if "http_status" not in exc.transport_meta:
                exc.transport_meta["http_status"] = exc.transport_meta.get(
                    "last_http_status"
                )
            raise

        if "http_status" not in transport_meta:
            transport_meta["http_status"] = transport_meta.get("last_http_status")

        text = self._parse_text(data)
        text = remove_thinking(text)
        text = apply_stop(text, request.stop)
        usage = data.get("usage") if isinstance(data, dict) else None
        return LLMResult(
            text=text,
            request_id=request.request_id,
            usage=usage if isinstance(usage, dict) else None,
            transport_meta={
                "provider": "openai_http",
                "base_url": self._normalized_base_url or self._base_url,
                "model": self._effective_model(request),
                "endpoint": self._endpoint,
                **transport_meta,
            },
            request_fingerprint=self._build_fingerprint(request),
        )
