"""Repair loop controller for deterministic validation failures."""

from __future__ import annotations

from typing import Dict, List, Optional

from agent.state import PipelineState
from validator.decision_engine import decide_next_action

_FORMAT_FIELD = "__format__"
_CONSISTENCY_FIELD = "__consistency__"


def _has_failures(state: PipelineState) -> bool:
    if state.format_errors:
        return True
    if state.consistency_flags:
        return True
    if any(state.semantic_errors.values()):
        return True
    if state.ontology_failures:
        return True
    return False


def _build_failures_by_field(state: PipelineState) -> Dict[str, List[str]]:
    failures: Dict[str, List[str]] = {}
    for field, failures_list in state.semantic_errors.items():
        if failures_list:
            failures[field] = list(failures_list)
    for field, failure_code in state.ontology_failures.items():
        if failure_code:
            failures.setdefault(field, []).append(failure_code)
    if state.format_errors:
        failures[_FORMAT_FIELD] = list(state.format_errors)
    if state.consistency_flags:
        failures[_CONSISTENCY_FIELD] = list(state.consistency_flags)
    return failures


def _clear_failures_for_field(state: PipelineState, field: str) -> None:
    state.semantic_errors.pop(field, None)
    state.ontology_failures.pop(field, None)
    if field == _FORMAT_FIELD:
        state.format_errors = []
    if field == _CONSISTENCY_FIELD:
        state.consistency_flags = []


def _increment_attempts(state: PipelineState, field: str) -> None:
    state.attempts_by_field[field] = state.attempts_by_field.get(field, 0) + 1


def _total_attempts(state: PipelineState) -> int:
    return sum(state.attempts_by_field.values())


def apply_repairs(
    state: PipelineState,
    decision_table: dict,
    max_total_repairs: Optional[int] = None,
) -> PipelineState:
    if not _has_failures(state):
        state.final_decision = "ACCEPT"
        return state

    while True:
        if not _has_failures(state):
            state.final_decision = "ACCEPT"
            return state

        if max_total_repairs is not None and _total_attempts(state) >= max_total_repairs:
            state.final_decision = "FLAGGED"
            if "max_repairs_exceeded" not in state.flags:
                state.flags.append("max_repairs_exceeded")
            return state

        failures_by_field = _build_failures_by_field(state)
        decision = decide_next_action(
            failures_by_field,
            state.attempts_by_field,
            decision_table,
        )

        if decision.decision_type == "ACCEPT":
            if _has_failures(state):
                break
            state.final_decision = "ACCEPT"
            return state

        if decision.decision_type == "ESCALATE":
            state.final_decision = "FLAGGED"
            if decision.failure_code and decision.failure_code not in state.flags:
                state.flags.append(decision.failure_code)
            return state

        field = decision.field
        if not field:
            state.final_decision = "FLAGGED"
            if decision.failure_code and decision.failure_code not in state.flags:
                state.flags.append(decision.failure_code)
            return state

        if decision.decision_type == "FALLBACK":
            if state.final_output is None:
                state.final_output = {}
            state.final_output[field] = decision.fallback_value
            _increment_attempts(state, field)
            state.repair_history.append(
                {
                    "failure_code": decision.failure_code,
                    "field": field,
                    "fallback_value": decision.fallback_value,
                }
            )
            _clear_failures_for_field(state, field)
            if decision.failure_code in state.consistency_flags:
                state.consistency_flags = [
                    flag
                    for flag in state.consistency_flags
                    if flag != decision.failure_code
                ]
            continue

        if decision.decision_type == "REPAIR":
            _increment_attempts(state, field)
            state.repair_history.append(
                {
                    "failure_code": decision.failure_code,
                    "field": field,
                    "repair_template": decision.repair_template,
                }
            )
            continue

        state.final_decision = "FLAGGED"
        if decision.failure_code and decision.failure_code not in state.flags:
            state.flags.append(decision.failure_code)
        return state

    if _has_failures(state):
        state.final_decision = "FLAGGED"
    else:
        state.final_decision = "ACCEPT"
    return state
