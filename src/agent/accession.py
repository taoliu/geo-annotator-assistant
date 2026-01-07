"""Helpers for enforcing authoritative accession identifiers."""

from __future__ import annotations

from typing import Dict, Optional


def override_accessions(
    parsed: Dict[str, str],
    true_gse: Optional[str],
    true_gsm: str,
) -> Dict[str, str]:
    if true_gse:
        parsed["gse_accession"] = true_gse
    parsed["gsm_accession"] = true_gsm
    return parsed
