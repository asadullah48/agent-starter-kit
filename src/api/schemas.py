"""Request/response schemas for the FastAPI layer."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="The user's message.")
    session_id: str = Field(
        default="default", description="Groups messages into one conversation."
    )


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    turn_count: int
