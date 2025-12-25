"""LLM service for generating responses."""

from typing import List, Optional

from openai import AsyncOpenAI

from app.core.config import settings
from app.core.exceptions import LLMError


class LLMService:
    """Service for LLM interactions."""

    def __init__(self) -> None:
        """Initialize LLM service."""
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def generate_response(
        self,
        messages: List[dict],
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate a response from the LLM.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens for response

        Returns:
            Generated response text

        Raises:
            LLMError: If LLM generation fails
        """
        try:
            all_messages = []
            if system_prompt:
                all_messages.append({"role": "system", "content": system_prompt})
            all_messages.extend(messages)

            response = await self.client.chat.completions.create(
                model=settings.llm_model,
                messages=all_messages,
                max_tokens=max_tokens or settings.response_tokens,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            raise LLMError(f"Failed to generate response: {e}") from e

    async def summarize(self, text: str, max_tokens: int = 200) -> str:
        """
        Summarize text using LLM.

        Args:
            text: Text to summarize
            max_tokens: Maximum tokens for summary

        Returns:
            Summary text

        Raises:
            LLMError: If summarization fails
        """
        try:
            response = await self.client.chat.completions.create(
                model=settings.llm_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that creates concise summaries. Extract key facts, entities, and important information.",
                    },
                    {"role": "user", "content": f"Summarize the following conversation:\n\n{text}"},
                ],
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            raise LLMError(f"Failed to summarize: {e}") from e

