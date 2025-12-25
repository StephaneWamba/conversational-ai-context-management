"""Database service for PostgreSQL operations."""

from typing import List, Optional
from uuid import UUID

import asyncpg
from app.core.config import settings
from app.core.exceptions import DatabaseError
from app.models.conversation import Conversation, ConversationSummary, Message


class DatabaseService:
    """Service for database operations."""

    def __init__(self) -> None:
        """Initialize database service."""
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self) -> None:
        """Connect to PostgreSQL database."""
        try:
            self.pool = await asyncpg.create_pool(
                settings.database_url,
                min_size=2,
                max_size=10,
            )
        except Exception as e:
            raise DatabaseError(f"Failed to connect to database: {e}") from e

    async def disconnect(self) -> None:
        """Disconnect from database."""
        if self.pool:
            await self.pool.close()

    async def create_conversation(
        self, user_id: str, session_id: str
    ) -> Conversation:
        """Create a new conversation."""
        if not self.pool:
            raise DatabaseError("Database not connected")

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO conversations (user_id, session_id)
                VALUES ($1, $2)
                RETURNING id, user_id, session_id, total_turns, total_tokens_used,
                          created_at, updated_at
                """,
                user_id,
                session_id,
            )
            return Conversation(
                id=row["id"],
                user_id=row["user_id"],
                session_id=row["session_id"],
                total_turns=row["total_turns"],
                total_tokens_used=row["total_tokens_used"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    async def get_conversation(self, conversation_id: UUID) -> Optional[Conversation]:
        """Get conversation by ID."""
        if not self.pool:
            raise DatabaseError("Database not connected")

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, user_id, session_id, total_turns, total_tokens_used,
                       created_at, updated_at
                FROM conversations
                WHERE id = $1
                """,
                conversation_id,
            )
            if not row:
                return None
            return Conversation(
                id=row["id"],
                user_id=row["user_id"],
                session_id=row["session_id"],
                total_turns=row["total_turns"],
                total_tokens_used=row["total_tokens_used"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    async def get_conversation_by_session(
        self, user_id: str, session_id: str
    ) -> Optional[Conversation]:
        """Get conversation by user_id and session_id."""
        if not self.pool:
            raise DatabaseError("Database not connected")

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, user_id, session_id, total_turns, total_tokens_used,
                       created_at, updated_at
                FROM conversations
                WHERE user_id = $1 AND session_id = $2
                ORDER BY created_at DESC
                LIMIT 1
                """,
                user_id,
                session_id,
            )
            if not row:
                return None
            return Conversation(
                id=row["id"],
                user_id=row["user_id"],
                session_id=row["session_id"],
                total_turns=row["total_turns"],
                total_tokens_used=row["total_tokens_used"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    async def add_message(
        self,
        conversation_id: UUID,
        role: str,
        content: str,
        turn_number: int,
        tokens_used: int = 0,
    ) -> Message:
        """Add a message to a conversation."""
        if not self.pool:
            raise DatabaseError("Database not connected")

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO messages (conversation_id, role, content, turn_number, tokens_used)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id, conversation_id, role, content, turn_number, tokens_used, created_at
                """,
                conversation_id,
                role,
                content,
                turn_number,
                tokens_used,
            )
            await conn.execute(
                """
                UPDATE conversations
                SET total_turns = total_turns + 1,
                    total_tokens_used = total_tokens_used + $1
                WHERE id = $2
                """,
                tokens_used,
                conversation_id,
            )
            return Message(
                id=row["id"],
                role=row["role"],
                content=row["content"],
                turn_number=row["turn_number"],
                tokens_used=row["tokens_used"],
                created_at=row["created_at"],
            )

    async def get_messages(
        self, conversation_id: UUID, limit: Optional[int] = None
    ) -> List[Message]:
        """Get messages for a conversation, ordered by turn_number ASC."""
        if not self.pool:
            raise DatabaseError("Database not connected")

        async with self.pool.acquire() as conn:
            query = """
                SELECT id, conversation_id, role, content, turn_number, tokens_used, created_at
                FROM messages
                WHERE conversation_id = $1
                ORDER BY turn_number ASC
            """
            if limit:
                query += f" LIMIT {limit}"
            rows = await conn.fetch(query, conversation_id)
            return [
                Message(
                    id=row["id"],
                    role=row["role"],
                    content=row["content"],
                    turn_number=row["turn_number"],
                    tokens_used=row["tokens_used"],
                    created_at=row["created_at"],
                )
                for row in rows
            ]

    async def get_recent_messages(
        self, conversation_id: UUID, limit: Optional[int] = None
    ) -> List[Message]:
        """Get most recent messages for a conversation, ordered by turn_number DESC."""
        if not self.pool:
            raise DatabaseError("Database not connected")

        async with self.pool.acquire() as conn:
            query = """
                SELECT id, conversation_id, role, content, turn_number, tokens_used, created_at
                FROM messages
                WHERE conversation_id = $1
                ORDER BY turn_number DESC
            """
            if limit:
                query += f" LIMIT {limit}"
            rows = await conn.fetch(query, conversation_id)
            # Reverse to get ASC order for the returned list
            messages = [
                Message(
                    id=row["id"],
                    role=row["role"],
                    content=row["content"],
                    turn_number=row["turn_number"],
                    tokens_used=row["tokens_used"],
                    created_at=row["created_at"],
                )
                for row in rows
            ]
            return list(reversed(messages))  # Return in ASC order

    async def create_summary(
        self,
        conversation_id: UUID,
        summary: str,
        compressed_tokens: int,
        turn_range_start: int,
        turn_range_end: int,
        key_facts: Optional[dict] = None,
    ) -> ConversationSummary:
        """Create a conversation summary."""
        if not self.pool:
            raise DatabaseError("Database not connected")

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO memory_summaries
                (conversation_id, summary, compressed_tokens, turn_range_start, turn_range_end, key_facts)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id, conversation_id, summary, compressed_tokens, turn_range_start,
                          turn_range_end, key_facts, created_at
                """,
                conversation_id,
                summary,
                compressed_tokens,
                turn_range_start,
                turn_range_end,
                key_facts,
            )
            return ConversationSummary(
                id=row["id"],
                summary=row["summary"],
                compressed_tokens=row["compressed_tokens"],
                turn_range_start=row["turn_range_start"],
                turn_range_end=row["turn_range_end"],
                key_facts=row["key_facts"],
                created_at=row["created_at"],
            )

    async def get_summaries(self, conversation_id: UUID) -> List[ConversationSummary]:
        """Get all summaries for a conversation."""
        if not self.pool:
            raise DatabaseError("Database not connected")

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, conversation_id, summary, compressed_tokens, turn_range_start,
                       turn_range_end, key_facts, created_at
                FROM memory_summaries
                WHERE conversation_id = $1
                ORDER BY turn_range_start ASC
                """,
                conversation_id,
            )
            return [
                ConversationSummary(
                    id=row["id"],
                    summary=row["summary"],
                    compressed_tokens=row["compressed_tokens"],
                    turn_range_start=row["turn_range_start"],
                    turn_range_end=row["turn_range_end"],
                    key_facts=row["key_facts"],
                    created_at=row["created_at"],
                )
                for row in rows
            ]

