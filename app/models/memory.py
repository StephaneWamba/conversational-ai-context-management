"""Memory data models."""

from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ShortTermMemory(BaseModel):
    """Short-term memory (recent turns)."""

    messages: List[dict] = Field(..., description="Recent messages")
    turn_count: int = Field(..., description="Number of turns in memory")


class LongTermMemory(BaseModel):
    """Long-term memory (summaries)."""

    summaries: List[dict] = Field(..., description="Conversation summaries")
    total_compressed_tokens: int = Field(
        default=0, description="Total compressed tokens")


class SemanticMemoryResult(BaseModel):
    """Semantic memory search result."""

    conversation_id: UUID = Field(..., description="Conversation ID")
    relevance_score: float = Field(..., description="Relevance score (0-1)")
    summary: str = Field(..., description="Conversation summary or excerpt")
    turn_count: int = Field(..., description="Number of turns in conversation")


class MemoryState(BaseModel):
    """Complete memory state for a conversation."""

    conversation_id: UUID = Field(..., description="Conversation ID")
    short_term: ShortTermMemory = Field(..., description="Short-term memory")
    long_term: Optional[LongTermMemory] = Field(
        default=None, description="Long-term memory")
    semantic: List[SemanticMemoryResult] = Field(
        default_factory=list, description="Semantic memory results"
    )
    total_context_tokens: int = Field(
        default=0, description="Total tokens in context")
