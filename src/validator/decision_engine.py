"""Deterministic decision engine for validation failures."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from .failure_codes import select_primary_failure_across_fields


@dataclass(frozen=True)
class Decision:
    decision_type: str
    field: Optional[str] = None
    failure_code: Optional[str] = None
    repair_template: Optional[str] = None
    fallback_value: Optional[str] = None
    severity: Optional[str] = None


def load_decision_table(path: str) -> Dict[str, Dict[str, Any]]:
    import yaml

    with open(path, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return data


def decide_next_action(
    failures_by_field: Dict[str, list[str]],
    attempts_by_field: Dict[str, int],
    decision_table: Dict[str, Dict[str, Any]],
) -> Decision:
    if not failures_by_field:
        return Decision(decision_type="ACCEPT")

    normalized_failures = {
        field: failures for field, failures in failures_by_field.items() if failures
    }
    if not normalized_failures:
        return Decision(decision_type="ACCEPT")

    field, failure_code = select_primary_failure_across_fields(normalized_failures)
    rule = decision_table.get(failure_code)
    if rule is None:
        return Decision(
            decision_type="ESCALATE",
            field=field,
            failure_code=failure_code,
            severity="high",
        )

    action = rule.get("action")
    rule_field = rule.get("field")
    target_field = rule_field if rule_field is not None else field
    repair_template = rule.get("repair_template")
    fallback_value = rule.get("fallback_value")
    severity = rule.get("severity")
    max_attempts = rule.get("max_attempts", 0)

    if action == "REPAIR":
        current_attempts = attempts_by_field.get(target_field, 0)
        if current_attempts >= max_attempts:
            if fallback_value is not None:
                return Decision(
                    decision_type="FALLBACK",
                    field=target_field,
                    failure_code=failure_code,
                    fallback_value=fallback_value,
                    severity=severity,
                )
            return Decision(
                decision_type="ESCALATE",
                field=target_field,
                failure_code=failure_code,
                severity=severity,
            )
        return Decision(
            decision_type="REPAIR",
            field=target_field,
            failure_code=failure_code,
            repair_template=repair_template,
            severity=severity,
        )

    if action == "FALLBACK":
        return Decision(
            decision_type="FALLBACK",
            field=target_field,
            failure_code=failure_code,
            fallback_value=fallback_value,
            severity=severity,
        )

    if action == "ESCALATE":
        return Decision(
            decision_type="ESCALATE",
            field=target_field,
            failure_code=failure_code,
            severity=severity,
        )

    if action == "ACCEPT":
        return Decision(
            decision_type="ACCEPT",
            field=target_field,
            failure_code=failure_code,
            severity=severity,
        )

    return Decision(
        decision_type="ESCALATE",
        field=target_field,
        failure_code=failure_code,
        severity=severity or "high",
    )
