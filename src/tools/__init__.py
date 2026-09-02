"""Tool registry.

Add a new tool by writing a module in this package that exports a
`TOOL_DEF` (the Anthropic tool schema) and a callable of the same name,
then registering both below. Nothing outside this file needs to change --
`agent/loop.py` only ever calls `get_tool_definitions()` and
`execute_tool()`.
"""

from __future__ import annotations

from typing import Any, Callable

from tools.calculator import TOOL_DEF as CALCULATOR_DEF, calculator
from tools.currency import TOOL_DEF as CURRENCY_DEF, convert_currency
from tools.knowledge_base import (
    TOOL_DEF as KNOWLEDGE_BASE_DEF,
    search_knowledge_base,
)

_REGISTRY: dict[str, Callable[..., str]] = {
    "calculator": calculator,
    "search_knowledge_base": search_knowledge_base,
    "convert_currency": convert_currency,
}

_DEFINITIONS: list[dict[str, Any]] = [CALCULATOR_DEF, KNOWLEDGE_BASE_DEF, CURRENCY_DEF]


def get_tool_definitions() -> list[dict[str, Any]]:
    """Return the tool schemas to pass as `tools=` on a Messages API call."""
    return _DEFINITIONS


def execute_tool(name: str, tool_input: dict[str, Any]) -> tuple[str, bool]:
    """Run a registered tool and return (result_text, is_error).

    Never raises -- a bad tool name, a bad argument, or a missing API key
    all become an `is_error=True` tool_result so Claude sees the failure
    and can retry or explain it, instead of crashing the whole agent turn.
    """
    tool = _REGISTRY.get(name)
    if tool is None:
        return f"Unknown tool: {name}", True
    try:
        return tool(**tool_input), False
    except Exception as exc:  # noqa: BLE001 -- deliberately broad: any tool failure becomes a tool_result, never an unhandled crash
        return f"Tool '{name}' failed: {exc}", True
