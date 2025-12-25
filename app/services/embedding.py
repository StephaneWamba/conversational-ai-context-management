"""Embedding service for generating vector embeddings."""

from typing import List

from openai import AsyncOpenAI

from app.core.config import settings
from app.core.exceptions import EmbeddingError


class EmbeddingService:
    """Service for generating embeddings."""

    def __init__(self) -> None:
        """Initialize embedding service."""
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors

        Raises:
            EmbeddingError: If embedding generation fails
        """
        try:
            response = await self.client.embeddings.create(
                model=settings.embedding_model,
                input=texts,
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            raise EmbeddingError(f"Failed to generate embeddings: {e}") from e

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector

        Raises:
            EmbeddingError: If embedding generation fails
        """
        embeddings = await self.generate_embeddings([text])
        return embeddings[0]

