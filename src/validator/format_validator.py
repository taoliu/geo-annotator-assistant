from __future__ import annotations

import json
from typing import Dict, List, Optional, Tuple

ERROR_INVALID_JSON = "invalid_json"
ERROR_NOT_OBJECT = "not_object"
ERROR_MISSING_KEYS = "missing_keys"
ERROR_EXTRA_KEYS = "extra_keys"
ERROR_NON_STRING = "non_string_value"
ERROR_EMPTY_VALUE = "empty_value"
ERROR_WORD_LIMIT = "word_limit_violation"

_ERROR_ORDER = [
    ERROR_INVALID_JSON,
    ERROR_NOT_OBJECT,
    ERROR_MISSING_KEYS,
    ERROR_EXTRA_KEYS,
    ERROR_NON_STRING,
    ERROR_EMPTY_VALUE,
    ERROR_WORD_LIMIT,
]

def _word_count(s: str) -> int:
    return len([w for w in s.strip().split() if w])

def _ordered_errors(seen: set[str]) -> List[str]:
    return [code for code in _ERROR_ORDER if code in seen]


def validate_format(raw_output: str, expected_keys: List[str]) -> Tuple[Optional[Dict[str, str]], List[str]]:
    """Validate raw LLM output format; returns (parsed_output, errors)."""
    errors: set[str] = set()
    try:
        obj = json.loads(raw_output)
    except Exception:
        return None, [ERROR_INVALID_JSON]
    if not isinstance(obj, dict):
        return None, [ERROR_NOT_OBJECT]

    keys = set(obj.keys())
    exp = set(expected_keys)
    missing = sorted(exp - keys)
    extra = sorted(keys - exp)
    if missing:
        errors.add(ERROR_MISSING_KEYS)
    if extra:
        errors.add(ERROR_EXTRA_KEYS)

    parsed: Dict[str, str] = {}
    for k in expected_keys:
        if k not in obj:
            continue
        v = obj[k]
        if not isinstance(v, str):
            errors.add(ERROR_NON_STRING)
            continue
        v2 = v.strip()
        if not v2:
            errors.add(ERROR_EMPTY_VALUE)
            continue
        if _word_count(v2) > 5:
            errors.add(ERROR_WORD_LIMIT)
        parsed[k] = v2

    return parsed, _ordered_errors(errors)
