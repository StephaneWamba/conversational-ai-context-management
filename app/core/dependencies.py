"""Dependency injection for services."""

from app.services.constraint_manager import ConstraintManager
from app.services.context_compressor import ContextCompressor
from app.services.database import DatabaseService
from app.services.embedding import EmbeddingService
from app.services.llm import LLMService
from app.services.memory_manager import MemoryManager
from app.services.semantic_memory import SemanticMemoryService
from app.services.token_manager import TokenManager


class ServiceContainer:
    """Container for service instances."""

    def __init__(self) -> None:
        """Initialize service container."""
        self.database = DatabaseService()
        self.embedding_service = EmbeddingService()
        self.llm_service = LLMService()
        self.semantic_memory = SemanticMemoryService()
        self.memory_manager = MemoryManager(
            database=self.database,
            semantic_memory=self.semantic_memory,
        )
        self.token_manager = TokenManager()
        self.context_compressor = ContextCompressor(
            llm_service=self.llm_service,
            token_manager=self.token_manager,
        )
        self.constraint_manager = ConstraintManager(database=self.database)

    async def initialize(self) -> None:
        """Initialize all services."""
        await self.database.connect()
        await self.semantic_memory.connect()
        await self.memory_manager.initialize()

    async def shutdown(self) -> None:
        """Shutdown all services."""
        await self.memory_manager.shutdown()
        await self.semantic_memory.disconnect()
        await self.database.disconnect()


services = ServiceContainer()

