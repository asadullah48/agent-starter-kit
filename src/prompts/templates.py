"""Small reusable prompt-building helpers.

Anything that formats data into text the model will read belongs here,
not inline in `agent/loop.py` -- it keeps prompt wording in one place and
makes each template independently testable.
"""

from __future__ import annotations


def format_tool_error(tool_name: str, error: str) -> str:
    """A consistent way to phrase a failed tool call back to the model."""
    return f"The '{tool_name}' tool failed: {error}. Consider trying a different approach."


def format_context_block(title: str, content: str) -> str:
    """Wrap retrieved context in a consistent, model-friendly block."""
    return f'<context title="{title}">\n{content}\n</context>'
