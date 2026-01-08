from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ui.overrides import (
    apply_overrides_to_record,
    clear_all_overrides,
    clear_overrides_for_gsm,
    overrides_for_gsm,
    set_override,
)


def _curation_record(gse: str, gsm: str) -> dict:
    return {
        "gse_accession": gse,
        "gsm_accession": gsm,
        "fields": {
            "data_type": "RNA-seq",
            "organism": "Homo sapiens",
            "tissue_type": "Blood",
            "cell_line": "No",
            "disease": "Healthy",
            "treatment": "No",
        },
        "raw": {"gse_accession": gse, "gsm_accession": gsm},
    }


def test_set_override_and_clear_for_gsm() -> None:
    overrides: dict = {}
    overrides = set_override(overrides, ("GSE1", "GSM1", "disease"), "Flu")
    overrides = set_override(overrides, ("GSE1", "GSM2", "disease"), "Cancer")

    assert overrides[("GSE1", "GSM1", "disease")] == "Flu"

    cleared = clear_overrides_for_gsm(overrides, "GSE1", "GSM1")
    assert ("GSE1", "GSM1", "disease") not in cleared
    assert ("GSE1", "GSM2", "disease") in cleared


def test_clear_all_overrides() -> None:
    overrides = {
        ("GSE1", "GSM1", "disease"): "Flu",
        ("GSE1", "GSM2", "tissue_type"): "Liver",
    }

    cleared = clear_all_overrides(overrides)

    assert cleared == {}


def test_apply_overrides_single_field() -> None:
    record = _curation_record("GSE1", "GSM1")

    effective = apply_overrides_to_record(record, {"tissue_type": "Liver"})

    assert effective is not None
    assert effective["tissue_type"] == "Liver"
    assert effective["disease"] == record["fields"]["disease"]


def test_apply_overrides_multiple_fields() -> None:
    record = _curation_record("GSE1", "GSM1")

    effective = apply_overrides_to_record(
        record,
        {"tissue_type": "Liver", "disease": "Cancer"},
    )

    assert effective is not None
    assert effective["tissue_type"] == "Liver"
    assert effective["disease"] == "Cancer"


def test_apply_overrides_list_values() -> None:
    record = _curation_record("GSE1", "GSM1")

    effective = apply_overrides_to_record(
        record,
        {"treatment": ["Drug A", "Drug B"]},
    )

    assert effective is not None
    assert effective["treatment"] == ["Drug A", "Drug B"]


def test_apply_overrides_deterministic_order() -> None:
    record = _curation_record("GSE1", "GSM1")
    overrides_one: dict = {}
    overrides_two: dict = {}

    order_one = [
        ("disease", "Flu"),
        ("tissue_type", "Liver"),
        ("treatment", ["Drug A", "Drug B"]),
    ]
    for field, value in order_one:
        overrides_one = set_override(overrides_one, ("GSE1", "GSM1", field), value)

    for field, value in reversed(order_one):
        overrides_two = set_override(overrides_two, ("GSE1", "GSM1", field), value)

    effective_one = apply_overrides_to_record(
        record, overrides_for_gsm(overrides_one, "GSE1", "GSM1")
    )
    effective_two = apply_overrides_to_record(
        record, overrides_for_gsm(overrides_two, "GSE1", "GSM1")
    )

    assert effective_one == effective_two
