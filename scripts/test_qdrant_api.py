"""Test Qdrant API directly."""

import asyncio
import sys
sys.path.insert(0, '/app')

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import NearestQuery

async def test():
    client = AsyncQdrantClient(url='http://qdrant:6333', check_compatibility=False)
    
    # Test query_points
    try:
        result = await client.query_points(
            collection_name='conversation_memory',
            query=NearestQuery(nearest=[0.1]*1536),
            limit=1,
        )
        print(f"query_points SUCCESS: {len(result.points) if result.points else 0} points")
        if result.points:
            print(f"  First point: score={result.points[0].score:.3f}, payload keys={list(result.points[0].payload.keys())}")
    except Exception as e:
        print(f"query_points FAILED: {e}")
        import traceback
        traceback.print_exc()
    
    await client.close()

asyncio.run(test())

