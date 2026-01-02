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


def test_happy_path() -> None:
    parsed, errors = validate_format('{"a": " ok ", "b": "two words"}', ["a", "b"])
    assert parsed == {"a": "ok", "b": "two words"}
    assert errors == []
