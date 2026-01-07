"""Repair loop controller for deterministic validation failures."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Dict, List, Optional

from agent.accession import override_accessions
from agent.state import PipelineState
from validator.format_validator import validate_format
from validator.decision_engine import decide_next_action

_FORMAT_FIELD = "__format__"
_CONSISTENCY_FIELD = "__consistency__"
_REQUIRED_KEYS: List[str] = [
    "gse_accession",
    "gsm_accession",
    "data_type",
    "organism",
    "tissue_type",
    "cell_line",
    "disease",
    "treatment",
]
_TERMINAL_FALLBACK_VALUES: Dict[str, set[str]] = {
    "disease": {"Unknown"},
    "tissue_type": {"Unknown"},
    "cell_line": {"No", "Unknown"},
    "organism": {"Unknown"},
    "data_type": {"Unknown"},
    "treatment": {"None"},
}


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


def _is_terminal_fallback(field: str, value: Optional[str]) -> bool:
    if value is None:
        return False
    return value in _TERMINAL_FALLBACK_VALUES.get(field, set())


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_repair_prompt(
    prompt_name: Optional[str],
    prompt_loader,
) -> str:
    if not prompt_name:
        raise ValueError("Repair template name is required for REPAIR actions.")
    if prompt_loader is None:
        from agent.prompts import load_prompt

        prompt_dir = str(_repo_root() / "prompts")
        return load_prompt(prompt_dir, prompt_name)
    if callable(prompt_loader):
        return prompt_loader(prompt_name)
    if isinstance(prompt_loader, dict):
        name = prompt_name if prompt_name.endswith(".txt") else f"{prompt_name}.txt"
        if prompt_name in prompt_loader:
            return prompt_loader[prompt_name]
        if name in prompt_loader:
            return prompt_loader[name]
    raise ValueError(f"Prompt template not found: {prompt_name}")


def apply_repairs(
    state: PipelineState,
    decision_table: dict,
    llm_client=None,
    context_text: Optional[str] = None,
    prompt_loader=None,
    max_total_repairs: Optional[int] = None,
    validation_callback: Optional[Callable[[PipelineState], None]] = None,
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
                state.final_decision = "ACCEPT"
                if decision.failure_code and decision.failure_code not in state.flags:
                    state.flags.append(decision.failure_code)
                return state
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

        if (
            decision.decision_type in {"FALLBACK", "REPAIR"}
            and field in state.terminal_fallback_fields
        ):
            _clear_failures_for_field(state, field)
            if decision.failure_code and decision.failure_code in state.consistency_flags:
                state.consistency_flags = [
                    flag for flag in state.consistency_flags
                    if flag != decision.failure_code
                ]
            if validation_callback is not None:
                validation_callback(state)
            continue

        if decision.decision_type == "FALLBACK":
            if state.final_output is None:
                state.final_output = {}

            val = decision.fallback_value
            if isinstance(val, str):
                val = val.strip()

            old = state.final_output.get(field)
            is_terminal = _is_terminal_fallback(field, val)

            # 🔴 TERMINAL FALLBACK GUARD
            if old == val:
                # Already at fallback value → do NOT count another attempt
                if is_terminal:
                    state.terminal_fallback_fields.add(field)
                _clear_failures_for_field(state, field)

                if decision.failure_code in state.consistency_flags:
                    state.consistency_flags = [
                        flag for flag in state.consistency_flags
                        if flag != decision.failure_code
                    ]

                if validation_callback is not None:
                    validation_callback(state)

                continue

            # Normal fallback (first time)
            state.final_output[field] = val
            _increment_attempts(state, field)
            if is_terminal:
                state.terminal_fallback_fields.add(field)

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
                    flag for flag in state.consistency_flags
                    if flag != decision.failure_code
                ]

            if validation_callback is not None:
                validation_callback(state)

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
            if llm_client is None or context_text is None:
                continue

            try:
                repair_template = _load_repair_prompt(
                    decision.repair_template,
                    prompt_loader,
                )
            except Exception:
                if "repair_template_missing" not in state.flags:
                    state.flags.append("repair_template_missing")
                if state.repair_history:
                    state.repair_history[-1]["template_missing"] = True
                continue
            previous_output = state.final_output or {}
            repair_prompt = (
                f"{repair_template}\n\nCONTEXT:\n{context_text}\n\nPREVIOUS_OUTPUT:\n"
                f"{json.dumps(previous_output, ensure_ascii=True)}"
            )
            raw_output = llm_client.generate(repair_prompt)
            state.llm_raw_outputs.append(raw_output)
            parsed_output, format_errors = validate_format(
                raw_output,
                _REQUIRED_KEYS,
            )
            state.format_errors = format_errors
            if parsed_output is not None:
                parsed_output = override_accessions(
                    parsed_output,
                    state.gse_accession,
                    state.gsm_accession,
                )
                state.llm_parsed_outputs.append(parsed_output)
            if parsed_output is None or format_errors:
                continue

            if state.final_output is None:
                state.final_output = {}

            # Only update the field we are repairing.
            if field in parsed_output:
                state.final_output[field] = parsed_output[field]

            override_accessions(
                state.final_output,
                state.gse_accession,
                state.gsm_accession,
            )


            if state.repair_history:
                state.repair_history[-1]["output_updated"] = True
            if validation_callback is not None:
                validation_callback(state)
                continue
            return state

        state.final_decision = "FLAGGED"
        if decision.failure_code and decision.failure_code not in state.flags:
            state.flags.append(decision.failure_code)
        return state

    if _has_failures(state):
        state.final_decision = "FLAGGED"
    else:
        state.final_decision = "ACCEPT"
    return state
