"""Application configuration using Pydantic settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # OpenAI configuration
    openai_api_key: str
    llm_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    # Database configuration
    database_url: str = "postgresql://conv_user:conv_pass@postgres:5432/conv_db"

    # Qdrant configuration
    qdrant_url: str = "http://qdrant:6333"
    qdrant_collection_name: str = "conversation_memory"

    # Redis configuration
    redis_url: str = "redis://redis:6379"

    # Service configuration
    service_name: str = "conversation-service"
    service_port: int = 8000

    # Memory configuration
    short_term_memory_size: int = 10  # Last N turns in Redis
    semantic_memory_limit: int = 5  # Top N relevant past conversations
    summary_interval: int = 10  # Summarize every N turns

    # Token management
    max_tokens_per_turn: int = 4000  # Max tokens for context + response
    system_prompt_tokens: int = 200  # Reserved for system prompt
    response_tokens: int = 1000  # Reserved for response
    context_budget: int = 2800  # Available for context (max - system - response)

    # Context compression
    compression_threshold: float = 0.8  # Compress when context > 80% of budget
    min_relevance_score: float = 0.5  # Minimum relevance for semantic memory (lowered for better recall)

    # Cache configuration
    cache_ttl: int = 3600  # 1 hour

    # Retry configuration
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    retry_backoff_multiplier: float = 2.0


settings = Settings()

