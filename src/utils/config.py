"""Centralized configuration, loaded from environment variables / .env."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    llm_provider: str
    model: str
    max_tokens: int
    memory_max_turns: int
    log_level: str
    ollama_base_url: str
    ollama_model: str
    apilayer_api_key: str


@lru_cache
def get_settings() -> Settings:
    return Settings(
        llm_provider=os.getenv("LLM_PROVIDER", "anthropic").lower(),
        model=os.getenv("CLAUDE_MODEL", "claude-opus-5"),
        max_tokens=int(os.getenv("CLAUDE_MAX_TOKENS", "4096")),
        memory_max_turns=int(os.getenv("AGENT_MEMORY_MAX_TURNS", "20")),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        ollama_model=os.getenv("OLLAMA_MODEL", "llama3.1"),
        apilayer_api_key=os.getenv("APILAYER_API_KEY", ""),
    )
