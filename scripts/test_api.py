"""Test script for the conversation API."""

import asyncio
import json
from uuid import UUID

import httpx


async def test_api():
    """Test the conversation API endpoints."""
    base_url = "http://localhost:8006"

    async with httpx.AsyncClient(timeout=30.0) as client:
        print("=" * 60)
        print("Testing Conversational AI Context Management API")
        print("=" * 60)

        # Test 1: Health Check
        print("\n1. Testing Health Endpoint...")
        try:
            response = await client.get(f"{base_url}/health")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                health_data = response.json() if response.headers.get("content-type") == "application/json" else eval(response.text)
                print(f"   Overall Status: {health_data.get('status', 'unknown')}")
                services = health_data.get('services', {})
                for service, status in services.items():
                    print(f"   - {service}: {status.get('status', 'unknown')}")
            else:
                print(f"   Error: {response.text}")
        except Exception as e:
            print(f"   Error: {e}")

        # Test 2: Readiness Check
        print("\n2. Testing Readiness Endpoint...")
        try:
            response = await client.get(f"{base_url}/ready")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                ready_data = response.json() if response.headers.get("content-type") == "application/json" else eval(response.text)
                print(f"   Ready: {ready_data.get('ready', False)}")
                print(f"   - PostgreSQL: {ready_data.get('postgres', False)}")
                print(f"   - Qdrant: {ready_data.get('qdrant', False)}")
                print(f"   - Redis: {ready_data.get('redis', False)}")
        except Exception as e:
            print(f"   Error: {e}")

        # Test 3: Create Conversation
        print("\n3. Testing Create Conversation...")
        conversation_id = None
        try:
            response = await client.post(
                f"{base_url}/api/conversations",
                json={
                    "user_id": "test_user_123",
                    "content": "Hello, I want to learn about Python programming. Can you help me?",
                },
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 201:
                data = response.json()
                conversation_id = data.get("id")
                print(f"   [OK] Conversation created: {conversation_id}")
                print(f"   - User ID: {data.get('user_id')}")
                print(f"   - Total Turns: {data.get('total_turns')}")
                print(f"   - Total Tokens: {data.get('total_tokens_used')}")
            else:
                print(f"   [ERROR] Status {response.status_code}: {response.text}")
        except Exception as e:
            print(f"   [ERROR] Error: {e}")

        if not conversation_id:
            print("\n   Cannot continue tests without a conversation ID.")
            return

        # Test 4: Send Message
        print("\n4. Testing Send Message...")
        try:
            response = await client.post(
                f"{base_url}/api/conversations/{conversation_id}/messages",
                json={
                    "user_id": "test_user_123",
                    "content": "How do I use async/await in Python?",
                },
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   [OK] Message sent successfully")
                print(f"   - Turn Number: {data.get('turn_number')}")
                print(f"   - Tokens Used: {data.get('tokens_used')}")
                print(f"   - Context Tokens: {data.get('context_tokens')}")
                print(f"   - Response Tokens: {data.get('response_tokens')}")
                print(f"   - Response Preview: {data.get('response', '')[:100]}...")
            else:
                print(f"   [ERROR] Status {response.status_code}: {response.text}")
        except Exception as e:
            print(f"   [ERROR] Error: {e}")

        # Test 5: Get Conversation
        print("\n5. Testing Get Conversation...")
        try:
            response = await client.get(f"{base_url}/api/conversations/{conversation_id}")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   [OK] Conversation retrieved")
                print(f"   - Total Turns: {data.get('total_turns')}")
                print(f"   - Total Tokens: {data.get('total_tokens_used')}")
            else:
                print(f"   [ERROR] Status {response.status_code}: {response.text}")
        except Exception as e:
            print(f"   [ERROR] Error: {e}")

        # Test 6: Get Memory State
        print("\n6. Testing Get Memory State...")
        try:
            response = await client.get(f"{base_url}/api/conversations/{conversation_id}/memory")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   [OK] Memory state retrieved")
                print(f"   - Short-term Turns: {data.get('short_term_turns')}")
                print(f"   - Long-term Summaries: {data.get('long_term_summaries')}")
                print(f"   - Semantic Results: {data.get('semantic_results')}")
                print(f"   - Total Context Tokens: {data.get('total_context_tokens')}")
            else:
                print(f"   [ERROR] Status {response.status_code}: {response.text}")
        except Exception as e:
            print(f"   [ERROR] Error: {e}")

        # Test 7: Send Multiple Messages (Test Context Management)
        print("\n7. Testing Multiple Messages (Context Management)...")
        for i in range(3):
            try:
                response = await client.post(
                    f"{base_url}/api/conversations/{conversation_id}/messages",
                    json={
                        "user_id": "test_user_123",
                        "content": f"Can you explain more about concept {i+1}?",
                    },
                )
                if response.status_code == 200:
                    data = response.json()
                    print(f"   [OK] Message {i+1} sent - Turn {data.get('turn_number')}, Tokens: {data.get('tokens_used')}")
                else:
                    print(f"   [ERROR] Message {i+1} failed: {response.text}")
            except Exception as e:
                error_msg = str(e).replace('\u2717', '[ERROR]')
                print(f"   [ERROR] Message {i+1} error: {error_msg}")

        print("\n" + "=" * 60)
        print("API Testing Complete!")
        print("=" * 60)
        print(f"\nConversation ID: {conversation_id}")
        print(f"Frontend URL: http://localhost:3000")
        print(f"API URL: {base_url}")


if __name__ == "__main__":
    asyncio.run(test_api())

