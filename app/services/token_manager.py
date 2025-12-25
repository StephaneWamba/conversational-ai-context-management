"""Token management service for budget tracking."""

import tiktoken

from app.core.config import settings
from app.core.exceptions import TokenBudgetError


class TokenManager:
    """Service for token counting and budget management."""

    def __init__(self) -> None:
        """Initialize token manager."""
        try:
            self.encoding = tiktoken.encoding_for_model(settings.llm_model)
        except KeyError:
            self.encoding = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens
        """
        return len(self.encoding.encode(text))

    def count_tokens_messages(self, messages: list) -> int:
        """
        Count tokens in a list of messages.

        Args:
            messages: List of message dictionaries with 'role' and 'content'

        Returns:
            Total number of tokens
        """
        total = 0
        for message in messages:
            total += 4  # Base tokens for message structure
            total += self.count_tokens(message.get("role", ""))
            total += self.count_tokens(message.get("content", ""))
        total += 2  # Final message separator
        return total

    def get_available_budget(
        self, system_tokens: int = 0, response_tokens: int = 0
    ) -> int:
        """
        Calculate available token budget for context.

        Args:
            system_tokens: Tokens used for system prompt
            response_tokens: Tokens reserved for response

        Returns:
            Available tokens for context
        """
        return (
            settings.max_tokens_per_turn
            - (system_tokens or settings.system_prompt_tokens)
            - (response_tokens or settings.response_tokens)
        )

    def check_budget(self, context_tokens: int, available_budget: int) -> None:
        """
        Check if context fits within budget.

        Args:
            context_tokens: Tokens in context
            available_budget: Available token budget

        Raises:
            TokenBudgetError: If context exceeds budget
        """
        if context_tokens > available_budget:
            raise TokenBudgetError(
                f"Context tokens ({context_tokens}) exceed available budget ({available_budget})"
            )
