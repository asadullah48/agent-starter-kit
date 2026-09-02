"""FastAPI surface for the agent.

One in-memory ConversationMemory per session_id -- fine for a starter kit
and local development; swap `_sessions` for a Redis- or DB-backed store
before running this with more than one worker process (and note that on
a serverless deployment each cold start gets a fresh, empty dict, so
`/chat` there is effectively single-turn -- see README's Live Demo
section).
"""

from __future__ import annotations

import os

from fastapi import FastAPI

from agent.loop import run_agent
from agent.memory import ConversationMemory
from api.schemas import ChatRequest, ChatResponse
from utils.config import get_settings
from utils.logging import get_logger

logger = get_logger(__name__)

app = FastAPI(title="agent-starter-kit", version="0.1.0")

_sessions: dict[str, ConversationMemory] = {}

_DEMO_REPLY = (
    "This is the public demo instance and has no LLM credentials configured, "
    "so I can't actually call a model here. Clone the repo, add your own "
    "ANTHROPIC_API_KEY (or set LLM_PROVIDER=ollama to run a local model for "
    "free), and run `python main.py --api` to try the full agent -- tools, "
    "memory, and all."
)


def _get_memory(session_id: str) -> ConversationMemory:
    if session_id not in _sessions:
        settings = get_settings()
        _sessions[session_id] = ConversationMemory(max_turns=settings.memory_max_turns)
    return _sessions[session_id]


def _demo_mode(settings) -> bool:
    """True when there's no way to actually reach an LLM from here."""
    if settings.llm_provider == "ollama":
        return False  # assume the operator has Ollama reachable if they chose it
    return not os.getenv("ANTHROPIC_API_KEY")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    settings = get_settings()
    if _demo_mode(settings):
        return ChatResponse(reply=_DEMO_REPLY, session_id=request.session_id, turn_count=0)

    memory = _get_memory(request.session_id)
    reply = run_agent(memory, request.message)
    logger.info("session=%s turn=%d", request.session_id, memory.turn_count())
    return ChatResponse(
        reply=reply, session_id=request.session_id, turn_count=memory.turn_count()
    )
