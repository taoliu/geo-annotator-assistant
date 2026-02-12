from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ui.checked import (
    build_visible_checked_updates,
    merge_visible_checked_updates,
)


def _visible_rows() -> list[dict[str, object]]:
    return [
        {"gse_accession": "GSE1", "gsm_accession": "GSM1"},
        {"gse_accession": "GSE1", "gsm_accession": "GSM2"},
    ]


def test_build_visible_checked_updates_ignores_invalid_rows() -> None:
    rows: list[dict[str, object]] = [
        {"gse_accession": "GSE1", "gsm_accession": "GSM1"},
        {"gse_accession": "GSE1", "gsm_accession": 123},
        {"gse_accession": None, "gsm_accession": "GSM2"},
    ]

    updates = build_visible_checked_updates(rows, True)

    assert updates == {("GSE1", "GSM1"): True}


def test_merge_visible_checked_updates_preserves_hidden_rows() -> None:
    existing = {
        ("GSE1", "GSM1"): False,
        ("GSE1", "GSM2"): True,
        ("GSE1", "GSM3"): False,
    }

    merged, changes = merge_visible_checked_updates(existing, _visible_rows(), True)

    assert merged == {
        ("GSE1", "GSM1"): True,
        ("GSE1", "GSM2"): True,
        ("GSE1", "GSM3"): False,
    }
    assert changes == {("GSE1", "GSM1"): True}


def test_merge_visible_checked_updates_can_clear_visible_rows() -> None:
    existing = {
        ("GSE1", "GSM1"): True,
        ("GSE1", "GSM2"): True,
        ("GSE1", "GSM3"): True,
    }

    merged, changes = merge_visible_checked_updates(existing, _visible_rows(), False)

    assert merged == {
        ("GSE1", "GSM1"): False,
        ("GSE1", "GSM2"): False,
        ("GSE1", "GSM3"): True,
    }
    assert changes == {
        ("GSE1", "GSM1"): False,
        ("GSE1", "GSM2"): False,
    }
