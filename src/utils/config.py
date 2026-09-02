"""Centralized configuration, loaded from environment variables / .env."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    model: str
    max_tokens: int
    memory_max_turns: int
    log_level: str


@lru_cache
def get_settings() -> Settings:
    return Settings(
        model=os.getenv("CLAUDE_MODEL", "claude-opus-5"),
        max_tokens=int(os.getenv("CLAUDE_MAX_TOKENS", "4096")),
        memory_max_turns=int(os.getenv("AGENT_MEMORY_MAX_TURNS", "20")),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )
