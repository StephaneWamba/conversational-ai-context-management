"""Semantic memory service for vector search."""

from typing import List, Optional
from uuid import UUID

import httpx
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from app.core.config import settings
from app.core.exceptions import VectorDBError
from app.models.memory import SemanticMemoryResult


class SemanticMemoryService:
    """Service for semantic memory storage and search."""

    def __init__(self) -> None:
        """Initialize semantic memory service."""
        self.client: Optional[AsyncQdrantClient] = None
        self.collection_name = settings.qdrant_collection_name

    async def connect(self) -> None:
        """Connect to Qdrant."""
        self.client = AsyncQdrantClient(
            url=settings.qdrant_url,
            timeout=30.0,
            check_compatibility=False,
        )
        await self._ensure_collection()

    async def disconnect(self) -> None:
        """Disconnect from Qdrant."""
        await self.client.close() if self.client else None

    async def _ensure_collection(self) -> None:
        """Ensure the collection exists."""
        if not self.client:
            return
        collections = await self.client.get_collections()
        if self.collection_name not in [col.name for col in collections.collections]:
            await self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=settings.embedding_dimensions,
                    distance=Distance.COSINE,
                ),
            )

    async def store_conversation(
        self,
        conversation_id: UUID,
        summary_id: UUID,
        user_id: str,
        text: str,
        embedding: List[float],
        turn_range_start: Optional[int] = None,
        turn_range_end: Optional[int] = None,
    ) -> None:
        """
        Store a conversation summary in semantic memory.

        Args:
            conversation_id: Conversation UUID
            summary_id: Summary UUID (from PostgreSQL)
            user_id: User identifier
            text: Conversation text or summary
            embedding: Embedding vector
            turn_range_start: Optional start turn number for the summary
            turn_range_end: Optional end turn number for the summary
        """
        await self._ensure_collection()
        await self.client.upsert(
            collection_name=self.collection_name,
            points=[
                PointStruct(
                    id=str(summary_id),
                    vector=embedding,
                    payload={
                        "conversation_id": str(conversation_id),
                        "summary_id": str(summary_id),
                        "user_id": user_id,
                        "text": text,
                        "turn_range_start": turn_range_start,
                        "turn_range_end": turn_range_end,
                    },
                )
            ],
        )

    async def search_relevant_conversations(
        self,
        query_embedding: List[float],
        user_id: str,
        limit: int = 5,
        min_score: float = 0.7,
    ) -> List[SemanticMemoryResult]:
        """
        Search for relevant past conversations.

        Args:
            query_embedding: Query embedding vector
            user_id: User identifier to filter by
            limit: Maximum number of results
            min_score: Minimum relevance score

        Returns:
            List of relevant conversation results
        """
        await self._ensure_collection()
        search_payload = {
            "vector": query_embedding,
            "limit": limit,
            "score_threshold": min_score,
            "with_payload": True,
            "with_vectors": False,
        }
        if user_id:
            search_payload["filter"] = {
                "must": [{"key": "user_id", "match": {"value": user_id}}]
            }

        async with httpx.AsyncClient(timeout=30.0) as http_client:
            response = await http_client.post(
                f"{settings.qdrant_url}/collections/{self.collection_name}/points/search",
                json=search_payload,
            )
            response.raise_for_status()
            search_results = response.json().get("result", [])

        results = []
        for item in search_results:
            payload = item.get("payload", {})
            if user_id and payload.get("user_id") != user_id:
                continue
            try:
                results.append(
                    SemanticMemoryResult(
                        conversation_id=UUID(payload.get("conversation_id")),
                        relevance_score=float(item.get("score", 0.0)),
                        summary=payload.get("text", ""),
                        turn_count=0,
                    )
                )
            except (ValueError, TypeError):
                continue
        return results
