from __future__ import annotations

import json
import re
from typing import Any, Callable, Dict, List, Optional, Tuple

ERROR_INVALID_JSON = "invalid_json"
ERROR_NOT_OBJECT = "not_object"
ERROR_MISSING_KEYS = "missing_keys"
ERROR_EXTRA_KEYS = "extra_keys"
ERROR_NON_STRING = "non_string_value"
ERROR_EMPTY_VALUE = "empty_value"
ERROR_WORD_LIMIT = "word_limit_violation"
FORMAT_SALVAGE_TRUNCATED_TREATMENT = "format_salvage_truncated_treatment"

_DEFAULT_SALVAGE_LIMIT = 512

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


def extract_json_candidate(text: str) -> Optional[str]:
    if not text:
        return None

    fenced_json = re.search(r"```json\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if fenced_json:
        return fenced_json.group(1).strip()

    fenced_any = re.search(r"```\s*(.*?)```", text, re.DOTALL)
    if fenced_any:
        return fenced_any.group(1).strip()

    start = text.find("{")
    if start == -1:
        return None

    depth = 0
    in_string = False
    escape = False
    for idx in range(start, len(text)):
        ch = text[idx]
        if in_string:
            if escape:
                escape = False
                continue
            if ch == "\\":
                escape = True
                continue
            if ch == '"':
                in_string = False
            continue

        if ch == '"':
            in_string = True
            continue
        if ch == "{":
            depth += 1
            continue
        if ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : idx + 1]
            continue

    return None


def _find_unescaped_quote(text: str) -> Optional[int]:
    escape = False
    for idx, ch in enumerate(text):
        if escape:
            escape = False
            continue
        if ch == "\\":
            escape = True
            continue
        if ch == '"':
            return idx
    return None


def _salvage_truncated_treatment(
    raw_output: str,
    expected_keys: List[str],
    max_chars: Optional[int],
) -> Optional[tuple[str, Dict[str, int | str]]]:
    if not raw_output or not expected_keys or expected_keys[-1] != "treatment":
        return None

    start = raw_output.find("{")
    if start == -1:
        return None

    treatment_match = re.search(r'"treatment"\s*:', raw_output[start:])
    if not treatment_match:
        return None
    treatment_key_start = start + treatment_match.start()
    prefix = raw_output[start:treatment_key_start]

    for key in expected_keys:
        if key == "treatment":
            continue
        if re.search(rf'"{re.escape(key)}"\s*:', prefix) is None:
            return None

    suffix = raw_output[treatment_key_start + treatment_match.end() :]
    for key in expected_keys:
        if key == "treatment":
            continue
        if re.search(rf'"{re.escape(key)}"\s*:', suffix):
            return None

    value_match = re.search(r'"treatment"\s*:\s*"', raw_output[start:])
    if not value_match:
        return None
    value_start = start + value_match.end()
    remainder = raw_output[value_start:]
    end_quote = _find_unescaped_quote(remainder)
    if end_quote is None:
        raw_value = remainder
    else:
        raw_value = remainder[:end_quote]

    original_length = len(raw_value)
    limit = max_chars if max_chars is not None else _DEFAULT_SALVAGE_LIMIT
    if limit <= 0:
        limit = original_length
    truncated_value = raw_value[:limit]

    prefix_clean = prefix.rstrip()
    if prefix_clean.endswith(","):
        prefix_clean = prefix_clean[:-1].rstrip()

    if not prefix_clean:
        return None

    needs_comma = not prefix_clean.endswith("{")
    separator = "," if needs_comma else ""
    candidate = f"{prefix_clean}{separator}\"treatment\": {json.dumps(truncated_value)}"
    candidate = f"{candidate}}}"

    try:
        obj = json.loads(candidate)
    except Exception:
        return None
    if not isinstance(obj, dict):
        return None

    meta = {
        "repair_type": FORMAT_SALVAGE_TRUNCATED_TREATMENT,
        "field": "treatment",
        "original_length": original_length,
        "truncated_length": len(truncated_value),
        "max_length": limit,
    }
    return candidate, meta


def _ordered_errors(seen: set[str]) -> List[str]:
    return [code for code in _ERROR_ORDER if code in seen]


def _word_limit_for_field(
    field: str,
    word_limits: Optional[Dict[str, int]],
) -> int:
    limit = 5
    if isinstance(word_limits, dict):
        limit = word_limits.get(field, 5)
    try:
        return int(limit)
    except (TypeError, ValueError):
        return 5


def build_format_error_details(
    parsed_output: Optional[Dict[str, str]],
    format_errors: List[str],
    expected_keys: List[str],
    *,
    stage: str,
    word_limits: Optional[Dict[str, int]] = None,
) -> List[Dict[str, Any]]:
    """Build deterministic per-field attribution details for format errors."""
    if not isinstance(parsed_output, dict) or not format_errors:
        return []

    details: List[Dict[str, Any]] = []
    error_set = set(format_errors)
    field_index = {field: idx for idx, field in enumerate(expected_keys)}

    if ERROR_WORD_LIMIT in error_set:
        for field in expected_keys:
            value = parsed_output.get(field)
            if not isinstance(value, str):
                continue
            limit = _word_limit_for_field(field, word_limits)
            observed = _word_count(value)
            if limit > 0 and observed > limit:
                details.append(
                    {
                        "code": ERROR_WORD_LIMIT,
                        "field": field,
                        "limit_used": limit,
                        "observed_word_count": observed,
                        "stage": stage,
                    }
                )

    details.sort(
        key=lambda item: (
            str(item.get("code") or ""),
            field_index.get(str(item.get("field") or ""), len(expected_keys)),
        )
    )
    return details


def validate_format(
    raw_output: str,
    expected_keys: List[str],
    *,
    word_limits: Optional[Dict[str, int]] = None,
    salvage_limit: Optional[int] = None,
    repair_recorder: Optional[Callable[[Dict[str, int | str]], None]] = None,
) -> Tuple[Optional[Dict[str, str]], List[str]]:
    """Validate raw LLM output format; returns (parsed_output, errors)."""
    errors: set[str] = set()
    try:
        obj = json.loads(raw_output)
    except Exception:
        candidate = extract_json_candidate(raw_output)
        if candidate is not None:
            try:
                obj = json.loads(candidate)
            except Exception:
                obj = None
        else:
            obj = None
        if obj is None:
            salvage = _salvage_truncated_treatment(
                raw_output,
                expected_keys,
                salvage_limit,
            )
            if salvage is None:
                return None, [ERROR_INVALID_JSON]
            candidate, meta = salvage
            try:
                obj = json.loads(candidate)
            except Exception:
                return None, [ERROR_INVALID_JSON]
            if repair_recorder is not None:
                repair_recorder(meta)
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
        limit = _word_limit_for_field(k, word_limits)
        if limit > 0 and _word_count(v2) > limit:
            errors.add(ERROR_WORD_LIMIT)
        parsed[k] = v2

    return parsed, _ordered_errors(errors)
