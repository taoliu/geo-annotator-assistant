"""Deterministic HTTP helpers for LLM transports."""

from __future__ import annotations

import json
import time
from typing import Any, Callable, Iterable

try:  # pragma: no cover - optional dependency
    import httpx  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    httpx = None

try:  # pragma: no cover - optional dependency
    import requests  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    requests = None

_RETRYABLE_STATUSES = {429, 500, 502, 503, 504}
_DEFAULT_BACKOFF_S = [0.5, 1.0, 2.0]


class LLMTransportError(Exception):
    def __init__(
        self,
        message: str,
        *,
        request_id: str | None,
        endpoint: str | None,
        retry_count: int,
        backoff_s: list[float],
        timeout_s: float,
        last_http_status: int | None,
        error_class: str,
        error_message_short: str,
        latency_ms: int | None = None,
    ) -> None:
        super().__init__(message)
        self.request_id = request_id
        self.endpoint = endpoint
        self.retry_count = retry_count
        self.backoff_s = backoff_s
        self.timeout_s = timeout_s
        self.last_http_status = last_http_status
        self.error_class = error_class
        self.error_message_short = error_message_short
        self.latency_ms = latency_ms
        self.transport_meta = {
            "retry_count": retry_count,
            "backoff_s": list(backoff_s),
            "timeout_s": timeout_s,
            "last_http_status": last_http_status,
            "error_class": error_class,
            "error_message_short": error_message_short,
            "latency_ms": latency_ms,
        }


class InvalidJSONResponseError(Exception):
    pass


def _short_message(text: str, limit: int = 200) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3] + "..."


def _build_backoff(max_retries: int, schedule: Iterable[float] | None) -> list[float]:
    base = list(schedule) if schedule is not None else list(_DEFAULT_BACKOFF_S)
    if max_retries <= 0:
        return []
    while len(base) < max_retries:
        base.append(base[-1] * 2 if base else 0.5)
    return base[:max_retries]


def _serialize_payload(payload: dict[str, Any]) -> str:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )


def _is_retryable_exception(exc: Exception) -> bool:
    if isinstance(exc, (TimeoutError, ConnectionError)):
        return True
    if httpx is not None:
        timeout_exc = getattr(httpx, "TimeoutException", None)
        request_exc = getattr(httpx, "RequestError", None)
        if timeout_exc is not None and isinstance(exc, timeout_exc):
            return True
        if request_exc is not None and isinstance(exc, request_exc):
            return True
    if requests is not None:
        timeout_exc = getattr(requests.exceptions, "Timeout", None)
        conn_exc = getattr(requests.exceptions, "ConnectionError", None)
        if timeout_exc is not None and isinstance(exc, timeout_exc):
            return True
        if conn_exc is not None and isinstance(exc, conn_exc):
            return True
    return False


def _post_json_via_httpx(
    url: str,
    payload_text: str,
    headers: dict[str, str],
    timeout_s: float,
) -> tuple[int, dict[str, Any] | None]:
    if httpx is None:  # pragma: no cover - dependency guard
        raise RuntimeError("httpx is not available")
    response = httpx.post(
        url,
        content=payload_text,
        headers=headers,
        timeout=timeout_s,
    )
    status = response.status_code
    if 200 <= status < 300:
        try:
            data = response.json()
        except Exception as exc:
            raise InvalidJSONResponseError("Invalid JSON response") from exc
        return status, data
    return status, None


def _post_json_via_requests(
    url: str,
    payload_text: str,
    headers: dict[str, str],
    timeout_s: float,
) -> tuple[int, dict[str, Any] | None]:
    if requests is None:  # pragma: no cover - dependency guard
        raise RuntimeError("requests is not available")
    response = requests.post(
        url,
        data=payload_text,
        headers=headers,
        timeout=timeout_s,
    )
    status = response.status_code
    if 200 <= status < 300:
        try:
            data = response.json()
        except Exception as exc:
            raise InvalidJSONResponseError("Invalid JSON response") from exc
        return status, data
    return status, None


def post_json_with_retries(
    url: str,
    payload: dict[str, Any],
    headers: dict[str, str],
    *,
    timeout_s: float,
    max_retries: int = 2,
    request_id: str | None = None,
    endpoint: str | None = None,
    backoff_schedule_s: Iterable[float] | None = None,
    post_func: Callable[[str, str, dict[str, str], float], tuple[int, dict[str, Any]]] | None = None,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> tuple[dict[str, Any], dict[str, Any]]:
    payload_text = _serialize_payload(payload)
    backoff = _build_backoff(max_retries, backoff_schedule_s)
    retries = 0
    backoff_slept: list[float] = []
    last_status: int | None = None
    start_time = time.perf_counter()

    while True:
        try:
            if post_func is not None:
                status, data = post_func(url, payload_text, headers, timeout_s)
            else:
                if httpx is not None:
                    status, data = _post_json_via_httpx(
                        url, payload_text, headers, timeout_s
                    )
                elif requests is not None:
                    status, data = _post_json_via_requests(
                        url, payload_text, headers, timeout_s
                    )
                else:  # pragma: no cover - dependency guard
                    raise RuntimeError(
                        "httpx or requests is required for HTTP transports"
                    )
            last_status = status
        except Exception as exc:
            error_class = exc.__class__.__name__
            error_message_short = _short_message(str(exc) or error_class)
            if _is_retryable_exception(exc) and retries < max_retries:
                delay = backoff[retries]
                backoff_slept.append(delay)
                sleep_fn(delay)
                retries += 1
                continue
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            raise LLMTransportError(
                f"HTTP transport failed: {error_message_short}",
                request_id=request_id,
                endpoint=endpoint,
                retry_count=retries,
                backoff_s=backoff_slept,
                timeout_s=timeout_s,
                last_http_status=last_status,
                error_class=error_class,
                error_message_short=error_message_short,
                latency_ms=latency_ms,
            ) from exc

        if 200 <= last_status < 300:
            if data is None:
                error_class = "InvalidJSONResponseError"
                error_message_short = "Invalid JSON response"
                latency_ms = int((time.perf_counter() - start_time) * 1000)
                raise LLMTransportError(
                    f"HTTP transport failed: {error_message_short}",
                    request_id=request_id,
                    endpoint=endpoint,
                    retry_count=retries,
                    backoff_s=backoff_slept,
                    timeout_s=timeout_s,
                    last_http_status=last_status,
                    error_class=error_class,
                    error_message_short=error_message_short,
                    latency_ms=latency_ms,
                )
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            transport_meta = {
                "retry_count": retries,
                "backoff_s": list(backoff_slept),
                "timeout_s": timeout_s,
                "last_http_status": last_status,
                "latency_ms": latency_ms,
            }
            return data, transport_meta

        if last_status in _RETRYABLE_STATUSES and retries < max_retries:
            delay = backoff[retries]
            backoff_slept.append(delay)
            sleep_fn(delay)
            retries += 1
            continue

        latency_ms = int((time.perf_counter() - start_time) * 1000)
        error_class = "HTTPStatusError"
        error_message_short = f"HTTP status {last_status}"
        raise LLMTransportError(
            f"HTTP transport failed: {error_message_short}",
            request_id=request_id,
            endpoint=endpoint,
            retry_count=retries,
            backoff_s=backoff_slept,
            timeout_s=timeout_s,
            last_http_status=last_status,
            error_class=error_class,
            error_message_short=error_message_short,
            latency_ms=latency_ms,
        )
