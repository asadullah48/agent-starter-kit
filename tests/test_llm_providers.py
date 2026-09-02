"""Tests for the Ollama provider adapter -- no network, no local Ollama
server required. Verifies the translation layers and the full call path
with httpx.post mocked."""

from unittest.mock import MagicMock, patch

from models.llm import (
    Block,
    _from_ollama_response,
    _to_ollama_messages,
    _to_ollama_tools,
    call_claude,
)


def test_to_ollama_messages_translates_plain_text_turns():
    messages = [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello"},
    ]
    out = _to_ollama_messages("be nice", messages)
    assert out[0] == {"role": "system", "content": "be nice"}
    assert out[1] == {"role": "user", "content": "hi"}
    assert out[2] == {"role": "assistant", "content": "hello"}


def test_to_ollama_messages_translates_tool_use_and_tool_result():
    messages = [
        {"role": "user", "content": "what is 2+2?"},
        {
            "role": "assistant",
            "content": [
                {"type": "tool_use", "name": "calculator", "input": {"expression": "2+2"}, "id": "t1"}
            ],
        },
        {
            "role": "user",
            "content": [{"type": "tool_result", "tool_use_id": "t1", "content": "4"}],
        },
    ]
    out = _to_ollama_messages("sys", messages)
    assistant_turn = next(m for m in out if m.get("tool_calls"))
    assert assistant_turn["tool_calls"][0]["function"]["name"] == "calculator"
    tool_turn = next(m for m in out if m["role"] == "tool")
    assert tool_turn["content"] == "4"


def test_to_ollama_tools_converts_schema_shape():
    tools = [
        {
            "name": "calculator",
            "description": "does math",
            "input_schema": {"type": "object", "properties": {}},
        }
    ]
    out = _to_ollama_tools(tools)
    assert out[0]["type"] == "function"
    assert out[0]["function"]["name"] == "calculator"
    assert out[0]["function"]["parameters"] == {"type": "object", "properties": {}}


def test_from_ollama_response_with_text_only():
    data = {"message": {"role": "assistant", "content": "hello there"}}
    result = _from_ollama_response(data)
    assert result.stop_reason == "end_turn"
    assert result.content == [Block(type="text", text="hello there")]


def test_from_ollama_response_with_tool_call():
    data = {
        "message": {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {"function": {"name": "calculator", "arguments": {"expression": "1+1"}}}
            ],
        }
    }
    result = _from_ollama_response(data)
    assert result.stop_reason == "tool_use"
    assert result.content[0].type == "tool_use"
    assert result.content[0].name == "calculator"
    assert result.content[0].input == {"expression": "1+1"}
    assert result.content[0].id  # synthesized, but must be non-empty


@patch("models.llm.httpx.post")
@patch("models.llm.get_settings")
def test_call_claude_routes_to_ollama_when_configured(mock_settings, mock_post):
    mock_settings.return_value = MagicMock(
        llm_provider="ollama",
        ollama_model="llama3.1",
        ollama_base_url="http://localhost:11434",
    )
    mock_response = MagicMock()
    mock_response.json.return_value = {"message": {"content": "hi from ollama"}}
    mock_post.return_value = mock_response

    result = call_claude(system="sys", messages=[{"role": "user", "content": "hey"}])

    assert result.content[0].text == "hi from ollama"
    mock_post.assert_called_once()
    called_url = mock_post.call_args.args[0]
    assert called_url == "http://localhost:11434/api/chat"
