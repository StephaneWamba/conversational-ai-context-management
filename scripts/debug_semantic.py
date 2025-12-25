"""Debug script to test semantic memory directly."""

import asyncio
import sys
sys.path.insert(0, '/app')

from app.services.semantic_memory import SemanticMemoryService
from app.services.embedding import EmbeddingService
from app.core.config import settings

async def main():
    """Test semantic memory directly."""
    semantic = SemanticMemoryService()
    embedding_service = EmbeddingService()
    
    await semantic.connect()
    
    # Check collection
    try:
        collection_info = await semantic.client.get_collection(settings.qdrant_collection_name)
        print(f"Collection '{settings.qdrant_collection_name}' has {collection_info.points_count} points")
        
        if collection_info.points_count > 0:
            # Get a sample point
            from qdrant_client.models import ScrollRequest
            scroll_result = await semantic.client.scroll(
                collection_name=settings.qdrant_collection_name,
                limit=1,
                with_payload=True,
                with_vectors=False,
            )
            if scroll_result[0]:
                point = scroll_result[0][0]
                print(f"Sample point payload: {point.payload}")
                print(f"Sample point user_id: {point.payload.get('user_id')}")
        
        # Test search
        test_query = "PostgreSQL database design"
        query_embedding = await embedding_service.generate_embedding(test_query)
        print(f"\nSearching for: '{test_query}'")
        print(f"Embedding size: {len(query_embedding)}")
        
        # Test without filter first using search API
        print("\n=== Test 1: Without user_id filter (using search) ===")
        results_no_filter = await semantic.client.search(
            collection_name=settings.qdrant_collection_name,
            query_vector=query_embedding,
            limit=5,
            query_filter=None,  # No filter
            score_threshold=0.1,  # Very low threshold
        )
        print(f"Found {len(results_no_filter) if results_no_filter else 0} results without filter")
        if results_no_filter:
            for i, point in enumerate(results_no_filter[:3]):
                print(f"  Result {i+1}: score={point.score:.3f}, user_id={point.payload.get('user_id')}")
        
        # Test with the actual user_id from the sample
        print("\n=== Test 2: With matching user_id ===")
        results = await semantic.search_relevant_conversations(
            query_embedding=query_embedding,
            user_id="user_1766651461688",  # Use the actual user_id from sample
            limit=5,
            min_score=0.1,  # Very low threshold
        )
        
        print(f"\nFound {len(results)} results")
        for i, result in enumerate(results):
            print(f"\nResult {i+1}:")
            print(f"  Conversation ID: {result.conversation_id}")
            print(f"  Relevance Score: {result.relevance_score:.3f}")
            print(f"  Summary: {result.summary[:100]}...")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await semantic.disconnect()

if __name__ == "__main__":
    asyncio.run(main())

