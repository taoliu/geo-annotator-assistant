from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agent import summarize_cli

_GSM_COLUMNS = [
    "gse_accession",
    "gsm_accession",
    "data_type",
    "organism",
    "tissue_type",
    "cell_line",
    "disease",
    "treatment",
]

_GSE_COLUMNS = [
    "gse_accession",
    "data_type",
    "organism",
    "tissue_type",
    "cell_line",
    "disease",
    "treatment",
]


def _write_jsonl(path: Path, records: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record))
            handle.write("\n")


def _curation_record(
    *,
    gse: str,
    gsm: str,
    data_type: str = "RNA-seq",
    organism: str = "Homo sapiens",
    tissue_type: str = "Blood",
    cell_line: str = "No",
    disease: str = "Healthy",
    treatment: str = "None",
) -> dict[str, str]:
    return {
        "gse_accession": gse,
        "gsm_accession": gsm,
        "data_type": data_type,
        "organism": organism,
        "tissue_type": tissue_type,
        "cell_line": cell_line,
        "disease": disease,
        "treatment": treatment,
    }


def _evidence_record(*, gse: str, gsm: str) -> dict[str, str]:
    return {
        "gse_accession": gse,
        "gsm_accession": gsm,
    }


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)
    return fieldnames, rows


def _write_gse_output_dir(base_dir: Path, gse: str, records: list[dict]) -> Path:
    gse_dir = base_dir / gse
    gse_dir.mkdir(parents=True, exist_ok=True)
    _write_jsonl(gse_dir / "curation.jsonl", records)
    _write_jsonl(
        gse_dir / "evidence.jsonl",
        [
            _evidence_record(gse=row["gse_accession"], gsm=row["gsm_accession"])
            for row in records
        ],
    )
    return gse_dir


def test_geo_gsm_annotate_summarize_help(capsys) -> None:
    with pytest.raises(SystemExit) as exc:
        summarize_cli.main(["--help"])
    assert exc.value.code == 0
    help_text = capsys.readouterr().out
    assert "--input-dir" in help_text
    assert "--overrides" in help_text
    assert "--output-dir" in help_text
    assert "--gsm-csv" in help_text
    assert "--gse-csv" in help_text
    assert "--strict" in help_text


def test_summarize_exports_csvs_and_applies_overrides_without_backend_calls(
    tmp_path: Path,
    capsys,
) -> None:
    input_dir = tmp_path / "outputs"
    input_dir.mkdir()
    gse100 = _write_gse_output_dir(
        input_dir,
        "GSE100",
        [
            _curation_record(gse="GSE100", gsm="GSM1"),
            _curation_record(gse="GSE100", gsm="GSM2", disease="Cancer"),
        ],
    )
    _write_gse_output_dir(
        input_dir,
        "GSE200",
        [
            _curation_record(
                gse="GSE200",
                gsm="GSM3",
                disease="Diabetes",
                treatment="Insulin",
            ),
        ],
    )
    _write_jsonl(
        gse100 / "overrides.jsonl",
        [
            {"gsm_accession": "GSM1", "field": "disease", "new_value": "Flu"},
            {"gsm_accession": "GSM1", "field": "treatment", "new_value": "DrugX"},
        ],
    )

    summarize_cli.main(["--input-dir", str(input_dir)])

    gsm_csv_path = input_dir / "gsm_annotations.csv"
    gse_csv_path = input_dir / "gse_summary.csv"
    assert gsm_csv_path.exists()
    assert gse_csv_path.exists()

    gsm_header, gsm_rows = _read_csv(gsm_csv_path)
    assert gsm_header == _GSM_COLUMNS
    assert len(gsm_rows) == 3
    gsm_row_map = {(row["gse_accession"], row["gsm_accession"]): row for row in gsm_rows}
    assert gsm_row_map[("GSE100", "GSM1")]["disease"] == "Flu"
    assert gsm_row_map[("GSE100", "GSM1")]["treatment"] == "DrugX"

    gse_header, gse_rows = _read_csv(gse_csv_path)
    assert gse_header == _GSE_COLUMNS
    assert len(gse_rows) == 2
    gse_row_map = {row["gse_accession"]: row for row in gse_rows}
    assert gse_row_map["GSE100"]["disease"] == "Cancer, Flu"
    assert gse_row_map["GSE100"]["treatment"] == "DrugX"
    assert gse_row_map["GSE200"]["disease"] == "Diabetes"
    assert gse_row_map["GSE200"]["treatment"] == "Insulin"

    stderr = capsys.readouterr().err
    assert f"INFO: summarize: scanning {input_dir}" in stderr
    assert "INFO: summarize: loaded 3 GSM records across 2 GSEs" in stderr
    assert "INFO: summarize: applied overrides from auto-detected overrides.jsonl (1 file(s))" in stderr


def test_summarize_explicit_overrides_take_precedence(tmp_path: Path) -> None:
    input_dir = tmp_path / "outputs"
    input_dir.mkdir()
    gse_dir = _write_gse_output_dir(
        input_dir,
        "GSE300",
        [_curation_record(gse="GSE300", gsm="GSM9")],
    )
    _write_jsonl(
        gse_dir / "overrides.jsonl",
        [{"gsm_accession": "GSM9", "field": "disease", "new_value": "AutoOverride"}],
    )
    explicit_overrides = tmp_path / "explicit_overrides.jsonl"
    _write_jsonl(
        explicit_overrides,
        [{"gsm_accession": "GSM9", "field": "disease", "new_value": "ExplicitOverride"}],
    )
    output_dir = tmp_path / "csv"

    summarize_cli.main(
        [
            "--input-dir",
            str(input_dir),
            "--overrides",
            str(explicit_overrides),
            "--output-dir",
            str(output_dir),
        ]
    )

    _, rows = _read_csv(output_dir / "gsm_annotations.csv")
    assert len(rows) == 1
    assert rows[0]["disease"] == "ExplicitOverride"


def test_summarize_warns_and_skips_invalid_gse_by_default(
    tmp_path: Path,
    capsys,
) -> None:
    input_dir = tmp_path / "outputs"
    input_dir.mkdir()
    _write_gse_output_dir(
        input_dir,
        "GSE400",
        [_curation_record(gse="GSE400", gsm="GSM1", disease="Cancer")],
    )
    bad_gse_dir = input_dir / "GSE401"
    bad_gse_dir.mkdir(parents=True, exist_ok=True)
    _write_jsonl(
        bad_gse_dir / "curation.jsonl",
        [_curation_record(gse="GSE401", gsm="GSM2", disease="Diabetes")],
    )

    summarize_cli.main(["--input-dir", str(input_dir)])

    _, rows = _read_csv(input_dir / "gsm_annotations.csv")
    assert len(rows) == 1
    assert rows[0]["gse_accession"] == "GSE400"
    stderr = capsys.readouterr().err
    assert "WARNING: summarize: skipping GSE401:" in stderr


def test_summarize_strict_fails_on_invalid_gse(tmp_path: Path, capsys) -> None:
    input_dir = tmp_path / "outputs"
    input_dir.mkdir()
    _write_gse_output_dir(
        input_dir,
        "GSE500",
        [_curation_record(gse="GSE500", gsm="GSM1")],
    )
    bad_gse_dir = input_dir / "GSE501"
    bad_gse_dir.mkdir(parents=True, exist_ok=True)
    _write_jsonl(
        bad_gse_dir / "curation.jsonl",
        [_curation_record(gse="GSE501", gsm="GSM2")],
    )

    with pytest.raises(SystemExit) as exc:
        summarize_cli.main(["--input-dir", str(input_dir), "--strict"])

    assert exc.value.code == 2
    stderr = capsys.readouterr().err
    assert "runtime error: strict mode: skipped GSE directories:" in stderr
