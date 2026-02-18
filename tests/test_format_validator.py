from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from validator.format_validator import (
    ERROR_EMPTY_VALUE,
    ERROR_EXTRA_KEYS,
    ERROR_INVALID_JSON,
    ERROR_MISSING_KEYS,
    ERROR_NON_STRING,
    ERROR_NOT_OBJECT,
    ERROR_WORD_LIMIT,
    build_format_error_details,
    validate_format,
)


def test_invalid_json() -> None:
    parsed, errors = validate_format("{", ["a"])
    assert parsed is None
    assert errors == [ERROR_INVALID_JSON]


def test_not_object() -> None:
    parsed, errors = validate_format('["a"]', ["a"])
    assert parsed is None
    assert errors == [ERROR_NOT_OBJECT]


def test_missing_keys() -> None:
    parsed, errors = validate_format('{"a": "value"}', ["a", "b"])
    assert parsed == {"a": "value"}
    assert errors == [ERROR_MISSING_KEYS]


def test_extra_keys() -> None:
    parsed, errors = validate_format('{"a": "value", "b": "extra"}', ["a"])
    assert parsed == {"a": "value"}
    assert errors == [ERROR_EXTRA_KEYS]


def test_non_string_value() -> None:
    parsed, errors = validate_format('{"a": 1}', ["a"])
    assert parsed == {}
    assert errors == [ERROR_NON_STRING]


def test_empty_value() -> None:
    parsed, errors = validate_format('{"a": "   "}', ["a"])
    assert parsed == {}
    assert errors == [ERROR_EMPTY_VALUE]


def test_word_limit_violation() -> None:
    parsed, errors = validate_format('{"a": "one two three four five six"}', ["a"])
    assert parsed == {"a": "one two three four five six"}
    assert errors == [ERROR_WORD_LIMIT]


def test_word_limit_disabled_for_field() -> None:
    parsed, errors = validate_format(
        '{"treatment": "one two three four five six"}',
        ["treatment"],
        word_limits={"treatment": 0},
    )
    assert parsed == {"treatment": "one two three four five six"}
    assert errors == []


def test_word_limit_custom_limit() -> None:
    parsed, errors = validate_format(
        '{"treatment": "one two three four five six seven eight nine ten eleven"}',
        ["treatment"],
        word_limits={"treatment": 10},
    )
    assert parsed == {"treatment": "one two three four five six seven eight nine ten eleven"}
    assert errors == [ERROR_WORD_LIMIT]


def test_happy_path() -> None:
    parsed, errors = validate_format('{"a": " ok ", "b": "two words"}', ["a", "b"])
    assert parsed == {"a": "ok", "b": "two words"}
    assert errors == []


def test_format_error_details_word_limit_default_fields() -> None:
    expected_keys = ["gse_accession", "gsm_accession", "tissue_type", "disease", "treatment"]
    parsed = {
        "gse_accession": "GSE2 7 1 0 8",
        "gsm_accession": "GSM7 0 9 1 7 5",
        "tissue_type": "Lung",
        "disease": "Healthy",
        "treatment": "None",
    }
    details = build_format_error_details(
        parsed,
        [ERROR_WORD_LIMIT],
        expected_keys,
        stage="initial",
        word_limits={"tissue_type": 10, "disease": 10, "treatment": 0},
    )

    assert details == [
        {
            "code": ERROR_WORD_LIMIT,
            "field": "gsm_accession",
            "limit_used": 5,
            "observed_word_count": 6,
            "stage": "initial",
        }
    ]
