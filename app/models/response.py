"""API response models."""

from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class MessageRequest(BaseModel):
    """Request to send a message."""

    content: str = Field(..., description="Message content", min_length=1)
    user_id: str = Field(..., description="User identifier")
    session_id: Optional[str] = Field(default=None, description="Session identifier")


class MessageResponse(BaseModel):
    """Response to a message."""

    conversation_id: UUID = Field(..., description="Conversation ID")
    message_id: UUID = Field(..., description="Message ID")
    response: str = Field(..., description="Assistant response")
    turn_number: int = Field(..., description="Turn number")
    tokens_used: int = Field(..., description="Total tokens used in this turn")
    context_tokens: int = Field(..., description="Tokens used for context")
    response_tokens: int = Field(..., description="Tokens used for response")


class ConversationResponse(BaseModel):
    """Conversation response."""

    id: UUID = Field(..., description="Conversation ID")
    user_id: str = Field(..., description="User identifier")
    session_id: str = Field(..., description="Session identifier")
    total_turns: int = Field(..., description="Total number of turns")
    total_tokens_used: int = Field(..., description="Total tokens used")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class MemoryResponse(BaseModel):
    """Memory state response."""

    conversation_id: UUID = Field(..., description="Conversation ID")
    short_term_turns: int = Field(..., description="Number of turns in short-term memory")
    long_term_summaries: int = Field(..., description="Number of summaries in long-term memory")
    semantic_results: int = Field(..., description="Number of semantic memory results")
    total_context_tokens: int = Field(..., description="Total tokens in context")
    total_turns: int = Field(..., description="Total number of turns in conversation")
    summaries: List[dict] = Field(default_factory=list, description="List of summaries with details")


class CreateConversationResponse(BaseModel):
    """Response when creating a new conversation."""

    conversation: ConversationResponse = Field(..., description="Conversation details")
    message: MessageResponse = Field(..., description="First assistant response")

