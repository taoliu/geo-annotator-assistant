"""Runtime tracing helpers for verbose CLI execution."""

from __future__ import annotations

import sys
from contextlib import contextmanager
from contextvars import ContextVar, Token
from dataclasses import dataclass
from typing import Iterator, TextIO


@dataclass(frozen=True)
class RuntimeTracer:
    enabled: bool = False
    stream: TextIO | None = None

    def info(self, message: str) -> None:
        if not self.enabled:
            return
        stream = self.stream if self.stream is not None else sys.stderr
        print(f"INFO: {message}", file=stream)


_ACTIVE_TRACER: ContextVar[RuntimeTracer] = ContextVar(
    "agent_runtime_tracer",
    default=RuntimeTracer(),
)


@contextmanager
def tracing_scope(enabled: bool) -> Iterator[None]:
    token: Token[RuntimeTracer] = _ACTIVE_TRACER.set(
        RuntimeTracer(enabled=enabled, stream=sys.stderr)
    )
    try:
        yield
    finally:
        _ACTIVE_TRACER.reset(token)


def _trace_info(message: str) -> None:
    _ACTIVE_TRACER.get().info(message)


def log_gse_start_processing(gse_accession: str) -> None:
    _trace_info(f"{gse_accession}: start processing")


def log_gse_using_local_soft(gse_accession: str) -> None:
    _trace_info(f"{gse_accession}: using local SOFT")


def log_gse_soft_download_start(gse_accession: str, transport: str) -> None:
    _trace_info(f"{gse_accession}: downloading SOFT via {transport}")


def log_gse_soft_download_completed(gse_accession: str) -> None:
    _trace_info(f"{gse_accession}: SOFT downloaded")


def log_gse_soft_parsed(gse_accession: str) -> None:
    _trace_info(f"{gse_accession}: SOFT parsed")


def log_gsm_calling_llm(gsm_accession: str) -> None:
    _trace_info(f"{gsm_accession}: calling LLM for annotation proposal")


def log_gsm_llm_received(gsm_accession: str) -> None:
    _trace_info(f"{gsm_accession}: LLM proposal received")


def log_gsm_validation_completed(gsm_accession: str) -> None:
    _trace_info(f"{gsm_accession}: validation completed")


def log_gsm_ontology_grounding_started(gsm_accession: str) -> None:
    _trace_info(f"{gsm_accession}: ontology grounding started")


def log_gsm_ontology_grounding_completed(gsm_accession: str) -> None:
    _trace_info(f"{gsm_accession}: ontology grounding completed")


def log_gsm_repair_loop_entered(gsm_accession: str) -> None:
    _trace_info(f"{gsm_accession}: entering repair loop")


def log_gsm_repair_loop_completed(gsm_accession: str) -> None:
    _trace_info(f"{gsm_accession}: repair loop completed")


def log_gsm_decision(gsm_accession: str, decision: str) -> None:
    _trace_info(f"{gsm_accession}: decision = {decision}")


def log_gse_outputs_written(gse_accession: str, output_dir: str) -> None:
    _trace_info(f"{gse_accession}: outputs written to {output_dir}")
