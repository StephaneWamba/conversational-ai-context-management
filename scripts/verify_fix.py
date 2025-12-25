"""Verify REST API fix is working."""
import asyncio
import sys
sys.path.insert(0, '/app')

from app.services.semantic_memory import SemanticMemoryService
from app.services.embedding import EmbeddingService

async def test():
    s = SemanticMemoryService()
    e = EmbeddingService()
    await s.connect()
    
    coll = await s.client.get_collection('conversation_memory')
    print(f'Collection has {coll.points_count} points')
    
    if coll.points_count > 0:
        emb = await e.generate_embedding('database design')
        results = await s.search_relevant_conversations(
            emb, 'user_1766651461688', limit=5, min_score=0.1
        )
        print(f'✅ Semantic search returned {len(results)} results')
        for r in results[:2]:
            print(f'  Score: {r.relevance_score:.3f}')
    else:
        print('No points in collection')
    
    await s.disconnect()

if __name__ == '__main__':
    asyncio.run(test())

