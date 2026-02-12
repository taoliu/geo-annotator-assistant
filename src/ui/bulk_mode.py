"""State helpers for one-shot bulk edit mode."""

from __future__ import annotations

from collections.abc import MutableMapping


def is_bulk_mode_active(
    state: MutableMapping[str, object],
    mode_key: str,
) -> bool:
    return bool(state.get(mode_key, False))


def activate_bulk_mode(
    state: MutableMapping[str, object],
    mode_key: str,
) -> None:
    state[mode_key] = True


def reset_bulk_mode_state(
    state: MutableMapping[str, object],
    *,
    mode_key: str,
    field_key: str,
    value_key: str,
) -> None:
    state.pop(field_key, None)
    state.pop(value_key, None)
    state[mode_key] = False


__all__ = [
    "activate_bulk_mode",
    "is_bulk_mode_active",
    "reset_bulk_mode_state",
]
