"""Loads the system prompt from prompts/system_prompt.md.

Keeping the prompt text in a `.md` file (not a Python string literal)
means non-engineers can edit tone and instructions without touching code,
and diffs on the prompt read as prose diffs, not code diffs.
"""

from __future__ import annotations

from pathlib import Path

_PROMPT_PATH = Path(__file__).parent / "system_prompt.md"
SYSTEM_PROMPT = _PROMPT_PATH.read_text(encoding="utf-8")
