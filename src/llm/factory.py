"""LLM factory and stub implementation."""

from __future__ import annotations

import json
import re
import time
from typing import Any, Dict, Optional

from llm.base import LLMClient, LLMRequest, LLMResult, compute_request_fingerprint


def _extract_accession(prompt: str, labels: list[str]) -> Optional[str]:
    for label in labels:
        match = re.search(rf"{re.escape(label)}\s*:\s*(\S+)", prompt)
        if match:
            return match.group(1)
    return None


class StubLLMClient:
    """Return a deterministic JSON payload for tests and smoke runs."""

    def __init__(self, cfg: Optional[Dict[str, Any]] = None) -> None:
        self._cfg = cfg or {}

    def generate(self, request: LLMRequest) -> LLMResult:
        start_time = time.perf_counter()
        prompt = request.prompt
        if self._cfg.get("stub_invalid_json"):
            text = "{invalid json"
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            return LLMResult(
                text=text,
                request_id=request.request_id,
                usage=None,
                transport_meta={
                    "provider": "stub",
                    "model_id": request.model,
                    "latency_ms": latency_ms,
                    "retry_count": 0,
                },
                request_fingerprint=compute_request_fingerprint(request),
            )

        gse_accession = _extract_accession(
            prompt,
            ["Series Accession", "GSE Accession"],
        )
        gsm_accession = _extract_accession(
            prompt,
            ["Sample ID", "Sample Accession", "GSM Accession"],
        )

        output = {
            "gse_accession": gse_accession or "GSE000000",
            "gsm_accession": gsm_accession or "GSM000000",
            "data_type": "RNA-seq",
            "organism": "Homo sapiens",
            "tissue_type": "Blood",
            "cell_line": "No",
            "disease": "Healthy",
            "treatment": "None",
        }
        text = json.dumps(output, ensure_ascii=True)
        latency_ms = int((time.perf_counter() - start_time) * 1000)
        return LLMResult(
            text=text,
            request_id=request.request_id,
            usage=None,
            transport_meta={
                "provider": "stub",
                "model_id": request.model,
                "latency_ms": latency_ms,
                "retry_count": 0,
            },
            request_fingerprint=compute_request_fingerprint(request),
        )


def create_llm_client(cfg: Optional[Dict[str, Any]] = None) -> LLMClient:
    cfg = cfg or {}
    transport = cfg.get("transport") or cfg.get("mode", "stub")
    if transport == "stub":
        return StubLLMClient(cfg)
    if transport in {"local_transformers", "transformers"}:
        from llm.local_transformers import LocalTransformersClient

        client = LocalTransformersClient(cfg)
        model_id = cfg.get("model_id") or cfg.get("model_path") or "Unknown"
        device = getattr(client, "_device", cfg.get("device", "auto"))
        print(f"[LLM] Initializing model: {model_id} on {device}")
        return client
    if transport == "openai_http":
        from llm.openai_http import OpenAIHttpClient

        return OpenAIHttpClient(cfg)
    if transport == "llama_cpp_http":
        from llm.llama_cpp_http import LlamaCppHttpClient

        return LlamaCppHttpClient(cfg)
    raise ValueError(f"Unsupported LLM transport: {transport}")
