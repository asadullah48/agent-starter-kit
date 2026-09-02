"""The agent's core execution loop.

Sends the conversation to Claude, executes any tool calls it asks for,
feeds the results back, and repeats until Claude produces a final answer
(or a safety cap on tool round-trips is hit).
"""

from __future__ import annotations

import logging

from agent.memory import ConversationMemory
from models.llm import call_claude
from prompts.system import SYSTEM_PROMPT
from tools import execute_tool, get_tool_definitions

logger = logging.getLogger(__name__)

MAX_TOOL_ITERATIONS = 8


def run_agent(memory: ConversationMemory, user_input: str) -> str:
    """Run one user turn to completion and return the agent's reply text.

    `memory` already holds prior turns; this call adds one more.
    """
    memory.begin_turn()
    memory.append({"role": "user", "content": user_input})

    tools = get_tool_definitions()

    for _ in range(MAX_TOOL_ITERATIONS):
        response = call_claude(
            system=SYSTEM_PROMPT,
            messages=memory.get_messages(),
            tools=tools,
        )

        if response.stop_reason == "pause_turn":
            # Server-side tool hit an internal iteration limit; resend as-is
            # so Claude can continue the same turn.
            memory.append({"role": "assistant", "content": response.content})
            continue

        tool_use_blocks = [b for b in response.content if b.type == "tool_use"]

        if not tool_use_blocks:
            reply = next(
                (b.text for b in response.content if b.type == "text"), ""
            )
            memory.append({"role": "assistant", "content": response.content})
            memory.end_turn()
            return reply

        memory.append({"role": "assistant", "content": response.content})

        tool_results = []
        for block in tool_use_blocks:
            logger.info("tool call: %s(%s)", block.name, block.input)
            result, is_error = execute_tool(block.name, block.input)
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                    "is_error": is_error,
                }
            )
        memory.append({"role": "user", "content": tool_results})

    # Safety cap hit: end the turn with whatever we have so memory stays
    # consistent, and tell the caller plainly rather than looping forever.
    memory.end_turn()
    return (
        "I wasn't able to finish after several tool calls -- could you "
        "rephrase or narrow the request?"
    )
