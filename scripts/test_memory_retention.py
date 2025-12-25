"""Automated test script for memory retention system."""

import asyncio
import json
import time
from typing import Dict, List, Optional
from uuid import UUID

import httpx


API_BASE_URL = "http://localhost:8006"


class MemoryRetentionTester:
    """Test memory retention across long conversations."""

    def __init__(self, api_url: str = API_BASE_URL):
        """Initialize tester."""
        self.api_url = api_url
        self.conversation_id: Optional[str] = None
        self.user_id = f"test_user_{int(time.time())}"
        self.conversation_history: List[Dict] = []  # Store full conversation
        self.test_results: List[Dict] = []
        self.expected_facts: Dict[str, str] = {}
        self.expected_constraints: Dict[str, any] = {}

    async def run_test(self) -> Dict:
        """Run the complete memory retention test."""
        print("=" * 80)
        print("MEMORY RETENTION TEST - 20 Messages")
        print("=" * 80)
        print()

        # Test messages designed to stress-test memory
        test_messages = [
            "My name is Alex, I'm 26 years old, and I live in Berlin.",
            "I work as a backend engineer, mostly using Python and FastAPI.",
            "I prefer short, structured answers with bullet points.",
            "I'm currently building a SaaS product for small e-commerce businesses.",
            "The SaaS is called ShopMind, and it focuses on customer analytics.",
            "Actually, correct something: I'm 27, not 26.",
            "I want ShopMind to support English and German, but English should be the default.",
            "I don't like overly technical explanations unless I explicitly ask for them.",
            "My main priority right now is user retention, not acquisition.",
            "Remember that I usually work late at night, between 9 PM and 1 AM.",
            "For ShopMind, I'm considering using PostgreSQL and Redis. Don't suggest MongoDB unless I ask.",
            "If I say \"dashboard\", I always mean a web dashboard, not mobile.",
            "In conversations, when I say \"metrics\", I'm referring to DAU, churn, and LTV only.",
            "I might later ask you to write emails or specs, and I want them to be concise and professional.",
            "Important: if you ever summarize my project, mention that it targets small e-commerce teams, not enterprises.",
            "Quick question: what stack am I using for my SaaS?",
            "Remind me what languages ShopMind supports and which one is default.",
            "It's 11:30 PM right now. Based on what you know, is this a normal working hour for me?",
            "Can you suggest metrics to track on my dashboard?",
            "Please summarize my profile and my project in 5 bullet points, respecting all my preferences.",
        ]

        # Expected facts and constraints
        self.expected_facts = {
            "name": "Alex",
            "age": "27",  # Corrected from 26
            "location": "Berlin",
            "profession": "backend engineer",
            "stack": ["Python", "FastAPI", "PostgreSQL", "Redis"],
            "project_name": "ShopMind",
            "project_focus": "customer analytics",
            "target_audience": "small e-commerce teams",
            "languages": ["English", "German"],
            "default_language": "English",
            "working_hours": "9 PM to 1 AM",
        }

        self.expected_constraints = {
            "answer_style": "short_bullet_points",
            "technical_depth": "minimal_unless_asked",
            "metrics_definition": ["DAU", "churn", "LTV"],
            "dashboard_definition": "web",
            "banned_tech": ["MongoDB"],
            "priority": "user retention",
        }

        # Run test
        try:
            await self._create_conversation(test_messages[0])
            await self._send_messages(test_messages)
            await self._validate_memory()
            await self._generate_report()
        except Exception as e:
            print(f"[ERROR] Test failed: {e}")
            import traceback
            traceback.print_exc()

        return {
            "conversation_id": self.conversation_id,
            "user_id": self.user_id,
            "test_timestamp": time.time(),
            "conversation_history": self.conversation_history,
            "memory_state": getattr(self, "memory_state", {}),
            "expected_facts": self.expected_facts,
            "expected_constraints": self.expected_constraints,
            "test_results": self.test_results,
        }

    async def _create_conversation(self, first_message: str) -> None:
        """Create a new conversation."""
        print("[1/4] Creating conversation...")
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.api_url}/api/conversations",
                json={
                    "user_id": self.user_id,
                    "content": first_message,
                },
            )
            response.raise_for_status()
            data = response.json()
            self.conversation_id = data["conversation"]["id"]

            # Store conversation turn
            self.conversation_history.append({
                "turn": 1,
                "user_message": first_message,
                "assistant_response": data["message"]["response"],
                "tokens_used": data["message"].get("tokens_used", 0),
                "context_tokens": data.get("context_tokens", 0),
                "response_tokens": data.get("response_tokens", 0),
                "timestamp": data["message"].get("created_at"),
            })

            print(f"    Conversation ID: {self.conversation_id}")
            print(
                f"    First response: {data['message']['response'][:100]}...")
            print()

    async def _send_messages(self, messages: List[str]) -> None:
        """Send all test messages."""
        print(f"[2/4] Sending {len(messages)} test messages...")
        async with httpx.AsyncClient(timeout=60.0) as client:
            for i, message in enumerate(messages[1:], start=2):
                print(f"    [{i}/{len(messages)}] Sending: {message[:50]}...")
                try:
                    response = await client.post(
                        f"{self.api_url}/api/conversations/{self.conversation_id}/messages",
                        json={
                            "user_id": self.user_id,
                            "content": message,
                        },
                    )
                    response.raise_for_status()
                    data = response.json()

                    # Store conversation turn
                    self.conversation_history.append({
                        "turn": i,
                        "user_message": message,
                        "assistant_response": data.get("response", ""),
                        "tokens_used": data.get("tokens_used", 0),
                        "context_tokens": data.get("context_tokens", 0),
                        "response_tokens": data.get("response_tokens", 0),
                        "timestamp": data.get("created_at"),
                    })

                    print(
                        f"        Response: {data.get('response', '')[:80]}...")
                    print(
                        f"        Tokens: {data.get('tokens_used', 0)} (context: {data.get('context_tokens', 0)})")
                except Exception as e:
                    # Store error turn
                    status_code = None
                    if 'response' in locals() and hasattr(response, 'status_code'):
                        status_code = response.status_code
                    self.conversation_history.append({
                        "turn": i,
                        "user_message": message,
                        "assistant_response": None,
                        "error": str(e),
                        "status_code": status_code,
                    })
                    print(f"        ERROR: {e}")
                await asyncio.sleep(1.0)  # Small delay between messages
        print()

    async def _validate_memory(self) -> None:
        """Validate memory retention."""
        print("[3/4] Validating memory retention...")
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Get memory state
            try:
                response = await client.get(
                    f"{self.api_url}/api/conversations/{self.conversation_id}/memory"
                )
                response.raise_for_status()
                memory = response.json()

                print(
                    f"    Short-term turns: {memory.get('short_term_turns', 0)}")
                print(
                    f"    Long-term summaries: {memory.get('long_term_summaries', 0)}")
                print(
                    f"    Semantic results: {memory.get('semantic_results', 0)}")
                print(f"    Total turns: {memory.get('total_turns', 0)}")
                print()

                # Store memory state
                self.memory_state = memory
            except Exception as e:
                print(f"    ERROR getting memory state: {e}")
                self.memory_state = {"error": str(e)}

            # Test 1: Check if summaries exist
            self._test(
                "Summaries Created",
                memory["long_term_summaries"] > 0,
                f"Expected > 0, got {memory['long_term_summaries']}",
            )

            # Test 2: Check total turns
            self._test(
                "Total Turns",
                memory["total_turns"] >= 20,
                f"Expected >= 20, got {memory['total_turns']}",
            )

            # Test 3: Query for specific facts
            test_queries = [
                ("What's my name?", "Alex"),
                ("How old am I?", "27"),  # Should be corrected value
                ("What's my project called?", "ShopMind"),
                ("What languages does ShopMind support?", "English"),
            ]

            for query, expected in test_queries:
                try:
                    response = await client.post(
                        f"{self.api_url}/api/conversations/{self.conversation_id}/messages",
                        json={
                            "user_id": self.user_id,
                            "content": query,
                        },
                    )
                    response.raise_for_status()
                    data = response.json()

                    # Store validation query turn
                    self.conversation_history.append({
                        "turn": len(self.conversation_history) + 1,
                        "user_message": query,
                        "assistant_response": data.get("response", ""),
                        "tokens_used": data.get("tokens_used", 0),
                        "context_tokens": data.get("context_tokens", 0),
                        "response_tokens": data.get("response_tokens", 0),
                        "validation_query": True,
                        "expected": expected,
                    })

                    answer = data.get("response", "").lower()
                    expected_lower = expected.lower()
                    passed = expected_lower in answer
                    self._test(
                        f"Recall: {query}",
                        passed,
                        f"Expected '{expected}' in answer, got: {data.get('response', '')[:100]}",
                    )
                except Exception as e:
                    self.conversation_history.append({
                        "turn": len(self.conversation_history) + 1,
                        "user_message": query,
                        "assistant_response": None,
                        "error": str(e),
                        "validation_query": True,
                        "expected": expected,
                    })
                await asyncio.sleep(0.5)

            # Test 4: Check constraint enforcement
            # Ask for metrics - should only suggest DAU, churn, LTV
            try:
                response = await client.post(
                    f"{self.api_url}/api/conversations/{self.conversation_id}/messages",
                    json={
                        "user_id": self.user_id,
                        "content": "What metrics should I track?",
                    },
                )
                response.raise_for_status()
                data = response.json()

                # Store validation query turn
                self.conversation_history.append({
                    "turn": len(self.conversation_history) + 1,
                    "user_message": "What metrics should I track?",
                    "assistant_response": data.get("response", ""),
                    "tokens_used": data.get("tokens_used", 0),
                    "context_tokens": data.get("context_tokens", 0),
                    "response_tokens": data.get("response_tokens", 0),
                    "validation_query": True,
                    "constraint_test": "metrics",
                })

                answer = data.get("response", "").lower()
                forbidden_metrics = ["retention rate",
                                     "session duration", "feedback"]
                violations = [m for m in forbidden_metrics if m in answer]
                self._test(
                    "Constraint Enforcement (Metrics)",
                    len(violations) == 0,
                    f"Found forbidden metrics in answer: {violations}",
                )
            except Exception as e:
                self.conversation_history.append({
                    "turn": len(self.conversation_history) + 1,
                    "user_message": "What metrics should I track?",
                    "assistant_response": None,
                    "error": str(e),
                    "validation_query": True,
                    "constraint_test": "metrics",
                })

            # Test 5: Check if correction is remembered
            try:
                response = await client.post(
                    f"{self.api_url}/api/conversations/{self.conversation_id}/messages",
                    json={
                        "user_id": self.user_id,
                        "content": "How old am I?",
                    },
                )
                response.raise_for_status()
                data = response.json()

                # Store validation query turn
                self.conversation_history.append({
                    "turn": len(self.conversation_history) + 1,
                    "user_message": "How old am I?",
                    "assistant_response": data.get("response", ""),
                    "tokens_used": data.get("tokens_used", 0),
                    "context_tokens": data.get("context_tokens", 0),
                    "response_tokens": data.get("response_tokens", 0),
                    "validation_query": True,
                    "correction_test": "age",
                })

                answer = data.get("response", "").lower()
                has_correct = "27" in answer or "twenty-seven" in answer
                has_wrong = "26" in answer or "twenty-six" in answer
                self._test(
                    "Correction Remembered (Age)",
                    has_correct and not has_wrong,
                    f"Expected age 27, answer: {data.get('response', '')[:100]}",
                )
            except Exception as e:
                self.conversation_history.append({
                    "turn": len(self.conversation_history) + 1,
                    "user_message": "How old am I?",
                    "assistant_response": None,
                    "error": str(e),
                    "validation_query": True,
                    "correction_test": "age",
                })

    def _test(self, name: str, passed: bool, message: str = "") -> None:
        """Record a test result."""
        status = "[PASS]" if passed else "[FAIL]"
        print(f"    {status} {name}")
        if not passed and message:
            print(f"        {message}")
        self.test_results.append(
            {"name": name, "passed": passed, "message": message}
        )

    async def _generate_report(self) -> None:
        """Generate test report."""
        print()
        print("[4/4] Generating test report...")
        print("=" * 80)
        print("TEST RESULTS SUMMARY")
        print("=" * 80)

        passed = sum(1 for r in self.test_results if r.get("passed"))
        total = len(self.test_results)
        failed = total - passed

        print(f"Total Tests: {total}")
        print(f"Passed: {passed} ({passed/total*100:.1f}%)")
        print(f"Failed: {failed} ({failed/total*100:.1f}%)")
        print()

        if failed > 0:
            print("FAILED TESTS:")
            for result in self.test_results:
                if not result.get("passed"):
                    print(f"  - {result['name']}: {result.get('message', '')}")
            print()

        print("=" * 80)
        print(f"Overall: {'PASS' if failed == 0 else 'FAIL'}")
        print("=" * 80)


async def main():
    """Main test function."""
    tester = MemoryRetentionTester()
    results = await tester.run_test()

    # Save full conversation to file
    output_file = f"memory_test_results_{int(time.time())}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nFull conversation saved to {output_file}")
    print(f"Total turns: {len(results.get('conversation_history', []))}")


if __name__ == "__main__":
    asyncio.run(main())
