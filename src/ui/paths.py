"""Input path validation for the UI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from pathlib import Path


@dataclass(frozen=True)
class InputPaths:
    input_dir: Path
    curation_path: Path
    evidence_path: Path
    suggestions_path: Path
    suggestions_present: bool
    audit_path: Path
    audit_present: bool
    gse_field_values_path: Path
    gse_field_values_present: bool


@dataclass(frozen=True)
class InputScanResult:
    input_dir: Path
    mode: Literal["single", "multi"]
    single_paths: InputPaths | None
    gse_paths: dict[str, InputPaths]
    skipped: dict[str, str]


def resolve_input_paths(input_dir: str) -> InputPaths:
    base_dir = Path(input_dir)
    if not base_dir.is_dir():
        raise ValueError(f"Input directory not found: {input_dir}")

    curation_path = base_dir / "curation.jsonl"
    evidence_path = base_dir / "evidence.jsonl"
    missing = [
        name
        for name, path in (
            ("curation.jsonl", curation_path),
            ("evidence.jsonl", evidence_path),
        )
        if not path.is_file()
    ]
    if missing:
        missing_list = ", ".join(missing)
        raise ValueError(
            f"Missing required file(s) in {input_dir}: {missing_list}"
        )

    suggestions_path = base_dir / "suggestions.jsonl"
    suggestions_present = suggestions_path.is_file()
    audit_path = base_dir / "audit.jsonl"
    audit_present = audit_path.is_file()
    gse_field_values_path = base_dir / "gse_field_values.jsonl"
    gse_field_values_present = gse_field_values_path.is_file()

    return InputPaths(
        input_dir=base_dir,
        curation_path=curation_path,
        evidence_path=evidence_path,
        suggestions_path=suggestions_path,
        suggestions_present=suggestions_present,
        audit_path=audit_path,
        audit_present=audit_present,
        gse_field_values_path=gse_field_values_path,
        gse_field_values_present=gse_field_values_present,
    )


def resolve_input_directory(input_dir: str) -> InputScanResult:
    base_dir = Path(input_dir)
    if not base_dir.is_dir():
        raise ValueError(f"Input directory not found: {input_dir}")

    curation_path = base_dir / "curation.jsonl"
    evidence_path = base_dir / "evidence.jsonl"
    if curation_path.is_file() and evidence_path.is_file():
        single_paths = resolve_input_paths(input_dir)
        return InputScanResult(
            input_dir=base_dir,
            mode="single",
            single_paths=single_paths,
            gse_paths={},
            skipped={},
        )

    gse_paths: dict[str, InputPaths] = {}
    skipped: dict[str, str] = {}
    for child in sorted(base_dir.iterdir()):
        if not child.is_dir():
            continue
        if not child.name.startswith("GSE"):
            continue
        try:
            gse_paths[child.name] = resolve_input_paths(str(child))
        except ValueError as exc:
            skipped[child.name] = str(exc)

    if not gse_paths:
        raise ValueError(
            f"No valid GSE* directories found in {input_dir}."
        )

    return InputScanResult(
        input_dir=base_dir,
        mode="multi",
        single_paths=None,
        gse_paths=gse_paths,
        skipped=skipped,
    )


__all__ = [
    "InputPaths",
    "InputScanResult",
    "resolve_input_paths",
    "resolve_input_directory",
]
