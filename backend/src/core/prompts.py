"""Utilities to load centralized prompts from prompts.yaml."""

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from .config import PROMPTS_FILE


@lru_cache(maxsize=1)
def load_prompts() -> dict[str, Any]:
    """Loads and caches prompts from YAML, returning an empty dict on failure."""
    prompts_path = Path(PROMPTS_FILE)

    try:
        with prompts_path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file) or {}
    except (FileNotFoundError, OSError, yaml.YAMLError):
        return {}

    if isinstance(data, dict):
        return data

    return {}


def get_prompt(key: str, default: str = "") -> str:
    """Gets a nested prompt value using dot notation, e.g. `tools.x.responses.y`."""
    current: Any = load_prompts()

    for part in key.split("."):
        if not isinstance(current, dict) or part not in current:
            return default
        current = current[part]

    return current if isinstance(current, str) else default