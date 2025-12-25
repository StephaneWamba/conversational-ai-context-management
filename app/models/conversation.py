"""Conversation data models."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class Message(BaseModel):
    """Message model."""

    id: Optional[UUID] = None
    role: str = Field(...,
                      description="Message role: user, assistant, or system")
    content: str = Field(..., description="Message content")
    turn_number: int = Field(..., description="Turn number in conversation")
    tokens_used: int = Field(
        default=0, description="Tokens used for this message")
    created_at: Optional[datetime] = None


class ConversationSummary(BaseModel):
    """Conversation summary model."""

    id: Optional[UUID] = None
    summary: str = Field(..., description="Compressed summary text")
    compressed_tokens: int = Field(
        default=0, description="Token count of summary")
    turn_range_start: int = Field(..., description="Start turn number")
    turn_range_end: int = Field(..., description="End turn number")
    key_facts: Optional[dict] = Field(
        default=None, description="Key facts and entities")
    created_at: Optional[datetime] = None


class Conversation(BaseModel):
    """Conversation model."""

    id: Optional[UUID] = None
    user_id: str = Field(..., description="User identifier")
    session_id: str = Field(..., description="Session identifier")
    total_turns: int = Field(default=0, description="Total number of turns")
    total_tokens_used: int = Field(default=0, description="Total tokens used")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ConversationWithMessages(Conversation):
    """Conversation with messages."""

    messages: List[Message] = Field(default_factory=list)


class ConversationWithMemory(ConversationWithMessages):
    """Conversation with messages and summaries."""

    summaries: List[ConversationSummary] = Field(default_factory=list)
