"""Health check service for dependency verification."""

import time
from typing import Dict

from app.core.config import settings
from app.services.database import DatabaseService
from app.services.semantic_memory import SemanticMemoryService


async def check_postgres(database: DatabaseService) -> Dict[str, any]:
    """
    Check PostgreSQL connectivity and health.

    Args:
        database: DatabaseService instance.

    Returns:
        Health status dictionary.
    """
    try:
        start_time = time.time()
        if not database.pool:
            return {"status": "unhealthy", "error": "Not connected", "latency_ms": 0}

        async with database.pool.acquire() as conn:
            await conn.execute("SELECT 1")
        latency_ms = (time.time() - start_time) * 1000

        return {
            "status": "healthy",
            "latency_ms": round(latency_ms, 2),
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "latency_ms": 0,
        }


async def check_qdrant(semantic_memory: SemanticMemoryService) -> Dict[str, any]:
    """
    Check Qdrant connectivity and health.

    Args:
        semantic_memory: SemanticMemoryService instance.

    Returns:
        Health status dictionary.
    """
    try:
        start_time = time.time()
        if not semantic_memory.client:
            return {"status": "unhealthy", "error": "Not connected", "latency_ms": 0}

        collections = await semantic_memory.client.get_collections()
        latency_ms = (time.time() - start_time) * 1000

        return {
            "status": "healthy",
            "latency_ms": round(latency_ms, 2),
            "collections": len(collections.collections),
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "latency_ms": 0,
        }


async def check_redis(memory_manager) -> Dict[str, any]:
    """
    Check Redis connectivity and health.

    Args:
        memory_manager: MemoryManager instance with redis_client.

    Returns:
        Health status dictionary.
    """
    try:
        start_time = time.time()
        if not memory_manager.redis_client:
            return {"status": "unhealthy", "error": "Not connected", "latency_ms": 0}

        await memory_manager.redis_client.ping()
        latency_ms = (time.time() - start_time) * 1000

        return {
            "status": "healthy",
            "latency_ms": round(latency_ms, 2),
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "latency_ms": 0,
        }


async def check_openai() -> Dict[str, any]:
    """
    Check OpenAI API connectivity.

    Returns:
        Health status dictionary.
    """
    try:
        if not settings.openai_api_key:
            return {"status": "not_configured", "error": "API key not set"}

        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.openai_api_key)

        start_time = time.time()
        await client.models.list()
        latency_ms = (time.time() - start_time) * 1000

        return {
            "status": "healthy",
            "latency_ms": round(latency_ms, 2),
        }
    except Exception as e:
        error_msg = str(e).lower()
        if "api key" in error_msg or "authentication" in error_msg:
            return {"status": "unhealthy", "error": "Invalid API key"}
        return {
            "status": "unhealthy",
            "error": str(e),
            "latency_ms": 0,
        }

