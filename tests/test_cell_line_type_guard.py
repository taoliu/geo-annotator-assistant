from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from validator import ontology_validator
from validator.ontology_match import OntologyMatch


def test_cell_line_cell_type_skips_grounder(monkeypatch) -> None:
    class DummyGrounder:
        def ground_cell_line(self, *args, **kwargs):
            raise AssertionError("ground_cell_line should not be called for cell types")

    monkeypatch.setattr(
        ontology_validator,
        "_cell_line_grounder",
        DummyGrounder(),
        raising=False,
    )

    matches, failures = ontology_validator.ground_all_fields(
        {"cell_line": "CD8+ T cells"},
        "",
        {},
    )

    assert matches["cell_line"].status == "FALLBACK"
    assert matches["cell_line"].alternates == []
    assert "cell_line" not in failures


def test_cell_line_hepg2_still_grounded(monkeypatch) -> None:
    called = {"count": 0}

    class DummyGrounder:
        def ground_cell_line(self, raw_value, context_text, config):
            called["count"] += 1
            return OntologyMatch(
                field="cell_line",
                raw_value=raw_value,
                ontology="Cellosaurus",
                status="MATCHED",
                matched_term_id="CVCL_0027",
                matched_label="HepG2",
                matched_source="Cellosaurus",
                match_type="label_exact",
                score=1.0,
                alternates=[],
            )

    monkeypatch.setattr(
        ontology_validator,
        "_cell_line_grounder",
        DummyGrounder(),
        raising=False,
    )

    matches, _ = ontology_validator.ground_all_fields(
        {"cell_line": "HepG2"},
        "",
        {},
    )

    assert called["count"] == 1
    assert matches["cell_line"].status == "MATCHED"


def test_cell_line_jurkat_still_grounded(monkeypatch) -> None:
    called = {"count": 0}

    class DummyGrounder:
        def ground_cell_line(self, raw_value, context_text, config):
            called["count"] += 1
            return OntologyMatch(
                field="cell_line",
                raw_value=raw_value,
                ontology="Cellosaurus",
                status="MATCHED",
                matched_term_id="CVCL_0065",
                matched_label="Jurkat",
                matched_source="Cellosaurus",
                match_type="label_exact",
                score=1.0,
                alternates=[],
            )

    monkeypatch.setattr(
        ontology_validator,
        "_cell_line_grounder",
        DummyGrounder(),
        raising=False,
    )

    matches, _ = ontology_validator.ground_all_fields(
        {"cell_line": "Jurkat"},
        "",
        {},
    )

    assert called["count"] == 1
    assert matches["cell_line"].status == "MATCHED"
