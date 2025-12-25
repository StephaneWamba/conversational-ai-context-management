"""Memory manager for hierarchical memory management."""

from typing import List, Optional
from uuid import UUID

import redis.asyncio as redis

from app.core.config import settings
from app.core.exceptions import CacheError, MemoryError
from app.models.memory import LongTermMemory, MemoryState, ShortTermMemory
from app.services.database import DatabaseService
from app.services.semantic_memory import SemanticMemoryService


class MemoryManager:
    """Manages hierarchical memory (short-term, long-term, semantic)."""

    def __init__(
        self,
        database: DatabaseService,
        semantic_memory: SemanticMemoryService,
    ) -> None:
        """Initialize memory manager."""
        self.database = database
        self.semantic_memory = semantic_memory
        self.redis_client: Optional[redis.Redis] = None

    async def initialize(self) -> None:
        """Initialize Redis connection."""
        self.redis_client = await redis.from_url(
            settings.redis_url, decode_responses=True
        )

    async def shutdown(self) -> None:
        """Shutdown Redis connection."""
        await self.redis_client.close() if self.redis_client else None

    async def add_message_to_short_term_memory(
        self, conversation_id: UUID, role: str, content: str, turn_number: int
    ) -> None:
        """
        Add a message to short-term memory (Redis cache).

        Args:
            conversation_id: Conversation ID
            role: Message role (user/assistant)
            content: Message content
            turn_number: Turn number
        """
        if not self.redis_client:
            return
        import json
        cache_key = f"conversation:{conversation_id}:messages"
        await self.redis_client.rpush(
            cache_key, json.dumps(
                {"role": role, "content": content, "turn_number": turn_number})
        )
        await self.redis_client.ltrim(cache_key, -settings.short_term_memory_size, -1)
        await self.redis_client.expire(cache_key, settings.cache_ttl)

    async def get_short_term_memory(
        self, conversation_id: UUID, limit: Optional[int] = None
    ) -> ShortTermMemory:
        """
        Get short-term memory (recent turns from Redis or database).

        Args:
            conversation_id: Conversation ID
            limit: Maximum number of turns to retrieve

        Returns:
            Short-term memory with recent messages
        """
        limit = limit or settings.short_term_memory_size
        if self.redis_client:
            cache_key = f"conversation:{conversation_id}:messages"
            cached = await self.redis_client.lrange(cache_key, -limit, -1)
            if cached:
                import json
                messages = [json.loads(msg) for msg in cached]
                return ShortTermMemory(messages=messages, turn_count=len(messages))

        db_messages = await self.database.get_recent_messages(conversation_id, limit=limit)
        messages = [
            {"role": msg.role, "content": msg.content,
                "turn_number": msg.turn_number}
            for msg in db_messages
        ]

        if self.redis_client and messages:
            import json
            cache_key = f"conversation:{conversation_id}:messages"
            await self.redis_client.delete(cache_key)
            for msg in messages:
                await self.redis_client.rpush(cache_key, json.dumps(msg))
            await self.redis_client.ltrim(cache_key, -settings.short_term_memory_size, -1)
            await self.redis_client.expire(cache_key, settings.cache_ttl)

        return ShortTermMemory(messages=messages, turn_count=len(messages))

    async def get_long_term_memory(
        self, conversation_id: UUID
    ) -> Optional[LongTermMemory]:
        """
        Get long-term memory (summaries from database).

        Args:
            conversation_id: Conversation ID

        Returns:
            Long-term memory with summaries, or None if no summaries exist
        """
        summaries = await self.database.get_summaries(conversation_id)
        if not summaries:
            return None
        return LongTermMemory(
            summaries=[
                {
                    "summary": s.summary,
                    "turn_range": (s.turn_range_start, s.turn_range_end),
                    "key_facts": s.key_facts,
                }
                for s in summaries
            ],
            total_compressed_tokens=sum(
                s.compressed_tokens for s in summaries),
        )

    async def get_memory_state(
        self,
        conversation_id: UUID,
        user_id: str,
        query_text: Optional[str] = None,
    ) -> MemoryState:
        """
        Get complete memory state for a conversation.

        Args:
            conversation_id: Conversation ID
            user_id: User identifier
            query_text: Optional query text for semantic search

        Returns:
            Complete memory state
        """
        short_term = await self.get_short_term_memory(conversation_id)
        long_term = await self.get_long_term_memory(conversation_id)

        semantic_results = []
        if query_text:
            from app.services.embedding import EmbeddingService
            embedding_service = EmbeddingService()
            query_embedding = await embedding_service.generate_embedding(query_text)
            semantic_results = await self.semantic_memory.search_relevant_conversations(
                query_embedding=query_embedding,
                user_id=user_id,
                limit=settings.semantic_memory_limit,
                min_score=settings.min_relevance_score,
            )

        from app.services.token_manager import TokenManager
        token_manager = TokenManager()
        context_tokens = token_manager.count_tokens_messages(
            short_term.messages)
        if long_term:
            context_tokens += sum(
                token_manager.count_tokens(s["summary"]) for s in long_term.summaries
            )

        return MemoryState(
            conversation_id=conversation_id,
            short_term=short_term,
            long_term=long_term,
            semantic=semantic_results,
            total_context_tokens=context_tokens,
        )
