"""Tests for the turn-based conversation memory trimming strategy."""

from agent.memory import ConversationMemory


def _add_turn(memory, user_text, reply_text):
    memory.begin_turn()
    memory.append({"role": "user", "content": user_text})
    memory.append({"role": "assistant", "content": reply_text})
    memory.end_turn()


def test_keeps_all_turns_under_the_limit():
    memory = ConversationMemory(max_turns=5)
    for i in range(3):
        _add_turn(memory, f"question {i}", f"answer {i}")
    assert memory.turn_count() == 3
    assert len(memory.get_messages()) == 6  # 2 messages per turn


def test_trims_oldest_turns_once_over_the_limit():
    memory = ConversationMemory(max_turns=2)
    for i in range(5):
        _add_turn(memory, f"question {i}", f"answer {i}")
    assert memory.turn_count() == 2
    messages = memory.get_messages()
    assert messages[0]["content"] == "question 3"
    assert messages[-1]["content"] == "answer 4"


def test_tool_round_trip_stays_intact_as_one_turn():
    """A turn with a tool_use/tool_result pair must be dropped or kept whole --
    never split, which would send an orphaned tool_result to the API."""
    memory = ConversationMemory(max_turns=1)
    memory.begin_turn()
    memory.append({"role": "user", "content": "what''s 2+2?"})
    memory.append({"role": "assistant", "content": [{"type": "tool_use", "id": "t1"}]})
    memory.append(
        {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "t1"}]}
    )
    memory.append({"role": "assistant", "content": "It''s 4."})
    memory.end_turn()

    _add_turn(memory, "and 3+3?", "It''s 6.")

    messages = memory.get_messages()
    assert len(messages) == 2
    assert messages[0]["content"] == "and 3+3?"
