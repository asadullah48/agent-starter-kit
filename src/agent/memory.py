"""Conversation memory for the agent.

Design decision -- how do we keep a long-running conversation from growing
without bound?

Two common strategies:
  1. Truncate: once the history passes a limit, drop the oldest turns.
     Cheap -- no extra API call -- but the agent "forgets" anything before
     the cutoff.
  2. Summarize: replace dropped turns with a short LLM-generated summary
     so older context survives in compressed form, at the cost of an
     extra call to Claude.

This starter kit ships strategy (1): it's predictable, needs no extra
network call, and is easy to unit test. A message list sent to the
Messages API must never start mid tool-call (a `tool_result` needs its
`tool_use` right before it), so memory groups messages into whole
"turns" -- one turn is everything that happened between a user message
and the agent's final reply, tool round-trips included -- and only ever
drops or keeps a turn as a unit.

Upgrade path: once this is running for real, swap `_trim()` for a
strategy-2 implementation that calls Claude to summarize the dropped
turns into a single system-style message instead of discarding them.
"""

from __future__ import annotations


class ConversationMemory:
    """Turn-based, size-bounded conversation history for one session."""

    def __init__(self, max_turns: int = 20) -> None:
        self.max_turns = max_turns
        self._turns: list[list[dict]] = []
        self._current: list[dict] | None = None

    def begin_turn(self) -> None:
        """Start buffering a new turn (call once per user message)."""
        self._current = []

    def append(self, message: dict) -> None:
        """Add one raw Messages-API message dict to the turn in progress."""
        if self._current is None:
            raise RuntimeError("begin_turn() must be called before append()")
        self._current.append(message)

    def end_turn(self) -> None:
        """Commit the buffered turn to history and enforce the size limit."""
        if self._current:
            self._turns.append(self._current)
        self._current = None
        self._trim()

    def _trim(self) -> None:
        """Drop the oldest whole turns once we exceed max_turns."""
        if len(self._turns) > self.max_turns:
            self._turns = self._turns[-self.max_turns:]

    def get_messages(self) -> list[dict]:
        """Flatten committed turns into the list the Messages API expects."""
        return [message for turn in self._turns for message in turn]

    def turn_count(self) -> int:
        return len(self._turns)
