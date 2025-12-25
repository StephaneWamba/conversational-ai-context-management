"""Context compression service for reducing token usage."""

from typing import List, Optional

from app.core.config import settings
from app.core.exceptions import CompressionError
from app.services.llm import LLMService
from app.services.token_manager import TokenManager


class ContextCompressor:
    """Service for compressing conversation context."""

    def __init__(
        self,
        llm_service: LLMService,
        token_manager: TokenManager,
    ) -> None:
        """Initialize context compressor."""
        self.llm_service = llm_service
        self.token_manager = token_manager

    async def compress_context(
        self, messages: List[dict], target_tokens: int
    ) -> List[dict]:
        """
        Compress context to fit within token budget.
        Preserves system messages (summaries, semantic results) and only compresses conversation messages.

        Args:
            messages: List of messages to compress
            target_tokens: Target token count

        Returns:
            Compressed messages list
        """
        current_tokens = self.token_manager.count_tokens_messages(messages)
        if current_tokens <= target_tokens:
            return messages

        try:
            system_messages = []
            conversation_messages = []

            for msg in messages:
                if (msg.get("role") == "system" and
                    ("summary" in msg.get("content", "").lower() or
                     "relevant past conversation" in msg.get("content", "").lower())):
                    system_messages.append(msg)
                else:
                    conversation_messages.append(msg)

            if not conversation_messages:
                return messages

            system_tokens = self.token_manager.count_tokens_messages(
                system_messages)
            available_for_conversation = max(0, target_tokens - system_tokens)

            if available_for_conversation <= 0:
                return messages

            conversation_tokens = self.token_manager.count_tokens_messages(
                conversation_messages)

            if conversation_tokens <= available_for_conversation:
                return system_messages + conversation_messages

            recent_count = max(1, len(conversation_messages) // 2)
            recent_messages = conversation_messages[-recent_count:]
            older_messages = conversation_messages[:-recent_count]

            if not older_messages:
                return system_messages + recent_messages

            # Create summary of older conversation messages
            older_text = "\n".join(
                [f"{msg['role']}: {msg['content']}" for msg in older_messages]
            )
            summary_prompt = f"""Create a comprehensive summary of the following conversation that preserves all important information:
- All facts, details, and information shared
- Key topics and discussions
- Any context that would be needed for future responses

Conversation:
{older_text}

Summary:"""

            summary_max_tokens = max(100, available_for_conversation // 2)
            summary = await self.llm_service.summarize(
                summary_prompt, max_tokens=summary_max_tokens
            )

            compressed = system_messages + [
                {"role": "system", "content": f"Previous conversation summary: {summary}"}
            ] + recent_messages

            return compressed
        except Exception as e:
            raise CompressionError(f"Failed to compress context: {e}") from e

    async def should_compress(self, context_tokens: int, budget: int) -> bool:
        """
        Check if context should be compressed.

        Args:
            context_tokens: Current context tokens
            budget: Available token budget

        Returns:
            True if compression is needed
        """
        threshold = int(budget * settings.compression_threshold)
        return context_tokens > threshold
