"""Prompt template loader for the agent."""

from __future__ import annotations

from pathlib import Path


def load_prompt(prompt_dir: str, prompt_name: str) -> str:
    """Load a single prompt template from a directory."""
    base_dir = Path(prompt_dir)
    if not base_dir.is_dir():
        raise ValueError(f"Prompt directory not found: {prompt_dir}")

    filename = prompt_name
    if not filename.endswith(".txt"):
        filename = f"{filename}.txt"
    path = base_dir / filename
    if not path.is_file():
        raise ValueError(f"Prompt template not found: {path}")

    with path.open("r", encoding="utf-8") as handle:
        return handle.read()


def load_prompts(prompt_dir: str) -> dict[str, str]:
    """Load all .txt prompt templates from a directory."""
    base_dir = Path(prompt_dir)
    if not base_dir.is_dir():
        raise ValueError(f"Prompt directory not found: {prompt_dir}")

    prompt_files = sorted(base_dir.glob("*.txt"))
    if not prompt_files:
        raise ValueError(f"No prompt templates found in: {prompt_dir}")

    prompts: dict[str, str] = {}
    for path in prompt_files:
        with path.open("r", encoding="utf-8") as handle:
            prompts[path.name] = handle.read()

    return prompts
