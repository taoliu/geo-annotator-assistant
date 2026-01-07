"""LLM factory and stub implementation."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, Optional

from llm.base import LLMClient


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

    def generate(self, prompt: str) -> str:
        if self._cfg.get("stub_invalid_json"):
            return "{invalid json"

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
        return json.dumps(output, ensure_ascii=True)


def create_llm_client(cfg: Optional[Dict[str, Any]] = None) -> LLMClient:
    cfg = cfg or {}
    mode = cfg.get("mode", "stub")
    if mode == "stub":
        return StubLLMClient(cfg)
    if mode in {"local_transformers", "transformers"}:
        from llm.local_transformers import LocalTransformersClient

        client = LocalTransformersClient(cfg)
        model_id = cfg.get("model_id") or cfg.get("model_path") or "Unknown"
        device = getattr(client, "_device", cfg.get("device", "auto"))
        print(f"[LLM] Initializing model: {model_id} on {device}")
        return client
    raise ValueError(f"Unsupported LLM mode: {mode}")
