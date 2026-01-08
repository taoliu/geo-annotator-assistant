from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ui import cli
from ui.paths import resolve_input_paths


def test_parse_args_requires_input_dir(capsys) -> None:
    with pytest.raises(SystemExit) as exc:
        cli.parse_args([])

    assert exc.value.code == 1
    err = capsys.readouterr().err
    assert "error:" in err
    assert "--input-dir" in err


def test_resolve_input_paths_requires_files(tmp_path: Path) -> None:
    (tmp_path / "curation.jsonl").write_text("{}\n", encoding="utf-8")

    with pytest.raises(ValueError) as exc:
        resolve_input_paths(str(tmp_path))

    message = str(exc.value)
    assert "Missing required file(s)" in message
    assert "evidence.jsonl" in message
