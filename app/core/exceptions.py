"""Custom exceptions for the application."""


class DatabaseError(Exception):
    """Raised when database operations fail."""

    pass


class VectorDBError(Exception):
    """Raised when vector database operations fail."""

    pass


class EmbeddingError(Exception):
    """Raised when embedding generation fails."""

    pass


class LLMError(Exception):
    """Raised when LLM operations fail."""

    pass


class CacheError(Exception):
    """Raised when cache operations fail."""

    pass


class MemoryError(Exception):
    """Raised when memory operations fail."""

    pass


class TokenBudgetError(Exception):
    """Raised when token budget is exceeded."""

    pass


class CompressionError(Exception):
    """Raised when context compression fails."""

    pass

