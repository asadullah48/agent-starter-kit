"""FastAPI surface for the agent.

One in-memory ConversationMemory per session_id -- fine for a starter kit
and local development; swap `_sessions` for a Redis- or DB-backed store
before running this with more than one worker process.
"""

from __future__ import annotations

from fastapi import FastAPI

from agent.loop import run_agent
from agent.memory import ConversationMemory
from api.schemas import ChatRequest, ChatResponse
from utils.config import get_settings
from utils.logging import get_logger

logger = get_logger(__name__)

app = FastAPI(title="agent-starter-kit", version="0.1.0")

_sessions: dict[str, ConversationMemory] = {}


def _get_memory(session_id: str) -> ConversationMemory:
    if session_id not in _sessions:
        settings = get_settings()
        _sessions[session_id] = ConversationMemory(max_turns=settings.memory_max_turns)
    return _sessions[session_id]


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    memory = _get_memory(request.session_id)
    reply = run_agent(memory, request.message)
    logger.info("session=%s turn=%d", request.session_id, memory.turn_count())
    return ChatResponse(
        reply=reply, session_id=request.session_id, turn_count=memory.turn_count()
    )
