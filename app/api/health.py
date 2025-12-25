"""Health check utilities."""

from typing import Dict

from app.services.health import (
    check_openai,
    check_postgres,
    check_qdrant,
    check_redis,
)


async def check_all_dependencies(
    database,
    semantic_memory,
    memory_manager,
) -> Dict:
    """
    Check all service dependencies.

    Args:
        database: DatabaseService instance.
        semantic_memory: SemanticMemoryService instance.
        memory_manager: MemoryManager instance.

    Returns:
        Dictionary with overall status and individual service statuses.
    """
    services = {}
    overall_status = "healthy"

    postgres_status = await check_postgres(database)
    services["postgres"] = postgres_status
    if postgres_status.get("status") != "healthy":
        overall_status = "unhealthy"

    qdrant_status = await check_qdrant(semantic_memory)
    services["qdrant"] = qdrant_status
    if qdrant_status.get("status") != "healthy":
        overall_status = "unhealthy"

    redis_status = await check_redis(memory_manager)
    services["redis"] = redis_status
    if redis_status.get("status") != "healthy":
        overall_status = "unhealthy"

    openai_status = await check_openai()
    services["openai"] = openai_status
    if openai_status.get("status") == "unhealthy":
        overall_status = "unhealthy"

    return {"status": overall_status, "services": services}


async def check_readiness(
    database,
    semantic_memory,
    memory_manager,
) -> Dict:
    """
    Check service readiness.

    Args:
        database: DatabaseService instance.
        semantic_memory: SemanticMemoryService instance.
        memory_manager: MemoryManager instance.

    Returns:
        Readiness status dictionary.
    """
    postgres_status = await check_postgres(database)
    qdrant_status = await check_qdrant(semantic_memory)
    redis_status = await check_redis(memory_manager)

    ready = (
        postgres_status.get("status") == "healthy"
        and qdrant_status.get("status") == "healthy"
        and redis_status.get("status") == "healthy"
    )

    return {
        "ready": ready,
        "postgres": postgres_status.get("status") == "healthy",
        "qdrant": qdrant_status.get("status") == "healthy",
        "redis": redis_status.get("status") == "healthy",
    }

