from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agent.context_fingerprint import compute_context_fingerprint


def test_context_fingerprint_normalizes_replicate_ids() -> None:
    context_a = (
        "Series Accession: GSE123\n"
        "Sample ID: GSM001\n"
        "Sample Title: patient_01\n"
        "Sample Characteristics: disease=healthy\n"
    )
    context_b = (
        "Series Accession: GSE123\n"
        "Sample ID: GSM002\n"
        "Sample Title: patient_02\n"
        "Sample Characteristics: disease=healthy\n"
    )

    assert compute_context_fingerprint(context_a) == compute_context_fingerprint(context_b)


def test_context_fingerprint_changes_on_semantic_context() -> None:
    context_a = (
        "Series Accession: GSE123\n"
        "Sample ID: GSM010\n"
        "Sample Title: patient_01\n"
        "Sample Characteristics: disease=healthy\n"
    )
    context_b = (
        "Series Accession: GSE123\n"
        "Sample ID: GSM011\n"
        "Sample Title: patient_02\n"
        "Sample Characteristics: disease=cancer\n"
    )

    assert compute_context_fingerprint(context_a) != compute_context_fingerprint(context_b)
