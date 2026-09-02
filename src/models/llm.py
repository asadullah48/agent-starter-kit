"""LLM provider wrapper.

Every call to an LLM in this project goes through `call_claude()` --
switch providers by setting LLM_PROVIDER in .env:

  - "anthropic" (default): Claude via the Anthropic SDK. Needs
    ANTHROPIC_API_KEY.
  - "ollama": any local model served by Ollama (https://ollama.com) --
    completely free, runs on your own machine, no API key. Needs Ollama
    running locally with a tool-capable model pulled, e.g.
    `ollama pull llama3.1`.

Both paths return the same shape to the rest of the codebase: an object
with `.stop_reason` and `.content` (a list of blocks exposing `.type`
and, depending on type, `.text` / `.name` / `.input` / `.id`).
`agent/loop.py` never checks which provider is active -- see LLMResponse
and Block below, which mirror just enough of the Anthropic SDK's own
response shape for the Ollama path to be a drop-in.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from typing import Any

import anthropic
import httpx

from utils.config import get_settings

logger = logging.getLogger(__name__)

_client: anthropic.Anthropic | None = None


def get_client() -> anthropic.Anthropic:
    """Lazily construct the Anthropic client (reads ANTHROPIC_API_KEY)."""
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


@dataclass
class Block:
    """A minimal stand-in for the Anthropic SDK's content block types."""

    type: str
    text: str = ""
    name: str = ""
    input: dict = field(default_factory=dict)
    id: str = ""


@dataclass
class LLMResponse:
    """A minimal stand-in for anthropic.types.Message."""

    stop_reason: str
    content: list[Block]


def call_claude(
    *,
    system: str,
    messages: list[dict],
    tools: list[dict] | None = None,
    max_tokens: int | None = None,
):
    """Send one chat request and return the response.

    Routes to Anthropic or Ollama based on `LLM_PROVIDER`. Raises on
    failure -- callers decide what to do about it rather than this
    wrapper hiding it (network errors and 429/5xx on the Anthropic path
    are already retried by the SDK itself, per its default `max_retries`).
    """
    settings = get_settings()
    if settings.llm_provider == "ollama":
        return _call_ollama(system=system, messages=messages, tools=tools)
    return _call_anthropic(
        system=system, messages=messages, tools=tools, max_tokens=max_tokens
    )


# --- Anthropic provider ----------------------------------------------------


def _call_anthropic(
    *,
    system: str,
    messages: list[dict],
    tools: list[dict] | None,
    max_tokens: int | None,
) -> anthropic.types.Message:
    settings = get_settings()
    client = get_client()

    kwargs: dict = dict(
        model=settings.model,
        max_tokens=max_tokens or settings.max_tokens,
        system=system,
        messages=messages,
    )
    if tools:
        kwargs["tools"] = tools

    try:
        return client.messages.create(**kwargs)
    except anthropic.NotFoundError:
        logger.error("Model '%s' not found -- check CLAUDE_MODEL.", settings.model)
        raise
    except anthropic.RateLimitError as exc:
        retry_after = exc.response.headers.get("retry-after", "unknown")
        logger.warning("Rate limited by the API; retry-after=%s", retry_after)
        raise
    except anthropic.APIConnectionError:
        logger.error("Network error calling the Anthropic API.")
        raise
    except anthropic.APIStatusError as exc:
        logger.error("Anthropic API error %s: %s", exc.status_code, exc.message)
        raise


# --- Ollama provider ---------------------------------------------------


def _call_ollama(
    *, system: str, messages: list[dict], tools: list[dict] | None
) -> LLMResponse:
    settings = get_settings()
    payload: dict[str, Any] = {
        "model": settings.ollama_model,
        "messages": _to_ollama_messages(system, messages),
        "stream": False,
    }
    if tools:
        payload["tools"] = _to_ollama_tools(tools)

    url = f"{settings.ollama_base_url}/api/chat"
    try:
        response = httpx.post(url, json=payload, timeout=120.0)
        response.raise_for_status()
    except httpx.ConnectError as exc:
        raise RuntimeError(
            f"Could not reach Ollama at {settings.ollama_base_url}. Is "
            f"`ollama serve` running, and did you `ollama pull "
            f"{settings.ollama_model}`?"
        ) from exc
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(
            f"Ollama returned {exc.response.status_code}: {exc.response.text}"
        ) from exc

    return _from_ollama_response(response.json())


def _block_type(block: Any) -> str | None:
    return block.get("type") if isinstance(block, dict) else getattr(block, "type", None)


def _to_ollama_messages(system: str, messages: list[dict]) -> list[dict]:
    """Translate our Anthropic-shaped history into Ollama's chat format."""
    out: list[dict] = [{"role": "system", "content": system}]

    for message in messages:
        role, content = message["role"], message["content"]

        if isinstance(content, str):
            out.append({"role": role, "content": content})
            continue

        text_parts: list[str] = []
        tool_calls: list[dict] = []
        for block in content:
            btype = _block_type(block)
            if btype == "text":
                text_parts.append(block["text"] if isinstance(block, dict) else block.text)
            elif btype == "tool_use":
                name = block["name"] if isinstance(block, dict) else block.name
                tool_input = block["input"] if isinstance(block, dict) else block.input
                tool_calls.append({"function": {"name": name, "arguments": tool_input}})
            elif btype == "tool_result":
                out.append({"role": "tool", "content": str(block.get("content", ""))})

        if tool_calls or text_parts:
            entry: dict = {"role": role, "content": " ".join(text_parts)}
            if tool_calls:
                entry["tool_calls"] = tool_calls
            out.append(entry)

    return out


def _to_ollama_tools(tools: list[dict]) -> list[dict]:
    return [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": t["input_schema"],
            },
        }
        for t in tools
    ]


def _from_ollama_response(data: dict) -> LLMResponse:
    message = data.get("message", {}) or {}
    blocks: list[Block] = []

    text = message.get("content") or ""
    if text:
        blocks.append(Block(type="text", text=text))

    for call in message.get("tool_calls", []) or []:
        fn = call.get("function", {})
        blocks.append(
            Block(
                type="tool_use",
                name=fn.get("name", ""),
                input=fn.get("arguments", {}) or {},
                id=f"ollama_{uuid.uuid4().hex[:12]}",
            )
        )

    stop_reason = "tool_use" if any(b.type == "tool_use" for b in blocks) else "end_turn"
    return LLMResponse(stop_reason=stop_reason, content=blocks)
