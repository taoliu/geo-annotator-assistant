"""Input path validation for the UI."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class InputPaths:
    input_dir: Path
    curation_path: Path
    evidence_path: Path
    suggestions_path: Path
    suggestions_present: bool


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

    return InputPaths(
        input_dir=base_dir,
        curation_path=curation_path,
        evidence_path=evidence_path,
        suggestions_path=suggestions_path,
        suggestions_present=suggestions_present,
    )
