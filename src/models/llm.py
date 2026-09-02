"""Thin wrapper around the Anthropic SDK.

Every call to Claude in this project goes through `call_claude()` -- swap
models, add retry/backoff, or point at a different provider by editing
only this file.
"""

from __future__ import annotations

import logging

import anthropic

from utils.config import get_settings

logger = logging.getLogger(__name__)

_client: anthropic.Anthropic | None = None


def get_client() -> anthropic.Anthropic:
    """Lazily construct the Anthropic client (reads ANTHROPIC_API_KEY)."""
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


def call_claude(
    *,
    system: str,
    messages: list[dict],
    tools: list[dict] | None = None,
    max_tokens: int | None = None,
) -> anthropic.types.Message:
    """Send one Messages API request and return the response.

    Raises the SDK's typed exceptions on failure (network errors and
    429/5xx are already retried by the SDK itself, per its default
    `max_retries`) -- callers decide what to do about it rather than this
    wrapper hiding the failure.
    """
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
