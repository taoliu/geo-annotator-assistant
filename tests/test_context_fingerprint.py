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


def test_context_fingerprint_normalizes_replicate_variants() -> None:
    base_lines = [
        "Series Accession: GSE123",
        "Sample Organism: Homo sapiens",
        "Sample Characteristics: disease=healthy",
    ]
    variants = [
        "Sample Title: rep 1",
        "Sample Title: replicate-1",
        "Sample Title: Rep1",
        "Sample Title: rep_1",
        "Sample Title: Replicate1",
    ]
    fingerprints = set()
    for idx, title in enumerate(variants, start=1):
        context = "\n".join(
            [
                *base_lines,
                f"Sample ID: GSM00{idx}",
                f"Sample Filename: GSM00{idx}_sample.txt",
                title,
            ]
        )
        fingerprints.add(compute_context_fingerprint(context))

    assert len(fingerprints) == 1


def test_context_fingerprint_changes_on_treatment_change() -> None:
    context_a = (
        "Series Accession: GSE123\n"
        "Sample ID: GSM010\n"
        "Sample Title: replicate 1\n"
        "Sample Characteristics: treatment=vehicle\n"
    )
    context_b = (
        "Series Accession: GSE123\n"
        "Sample ID: GSM011\n"
        "Sample Title: replicate 2\n"
        "Sample Characteristics: treatment=drug\n"
    )

    assert compute_context_fingerprint(context_a) != compute_context_fingerprint(context_b)


def test_context_fingerprint_normalizes_keyword_ids() -> None:
    context_a = (
        "Series Accession: GSE123\n"
        "Sample ID: GSM020\n"
        "Sample Title: donor_001\n"
        "Sample Characteristics: disease=healthy\n"
    )
    context_b = (
        "Series Accession: GSE123\n"
        "Sample ID: GSM021\n"
        "Sample Title: donor_002\n"
        "Sample Characteristics: disease=healthy\n"
    )

    assert compute_context_fingerprint(context_a) == compute_context_fingerprint(context_b)


def test_context_fingerprint_normalizes_replication_markers() -> None:
    base = (
        "Series Accession: GSE123\n"
        "Sample Characteristics: disease=healthy\n"
    )
    rep1 = (
        f"{base}"
        "Sample ID: GSM030\n"
        "Sample Title: Rep1\n"
    )
    rep2 = (
        f"{base}"
        "Sample ID: GSM031\n"
        "Sample Title: Rep2\n"
    )
    biorep1 = (
        f"{base}"
        "Sample ID: GSM032\n"
        "Sample Title: BioRep1\n"
    )
    biorep2 = (
        f"{base}"
        "Sample ID: GSM033\n"
        "Sample Title: BioRep2\n"
    )

    assert compute_context_fingerprint(rep1) == compute_context_fingerprint(rep2)
    assert compute_context_fingerprint(biorep1) == compute_context_fingerprint(biorep2)


def test_context_fingerprint_normalizes_patient_id_with_suffix() -> None:
    context_a = (
        "Series Accession: GSE123\n"
        "Sample ID: GSM040\n"
        "Sample Title: PTL_patient_O23_1\n"
        "Sample Characteristics: disease=healthy\n"
    )
    context_b = (
        "Series Accession: GSE123\n"
        "Sample ID: GSM041\n"
        "Sample Title: PTL_patient_R-27_1\n"
        "Sample Characteristics: disease=healthy\n"
    )

    assert compute_context_fingerprint(context_a) == compute_context_fingerprint(context_b)


def test_context_fingerprint_preserves_timepoint_tokens() -> None:
    context_a = (
        "Series Accession: GSE123\n"
        "Sample ID: GSM050\n"
        "Sample Title: Control_T1\n"
        "Sample Characteristics: disease=healthy\n"
    )
    context_b = (
        "Series Accession: GSE123\n"
        "Sample ID: GSM051\n"
        "Sample Title: Control_T2\n"
        "Sample Characteristics: disease=healthy\n"
    )

    assert compute_context_fingerprint(context_a) != compute_context_fingerprint(context_b)
