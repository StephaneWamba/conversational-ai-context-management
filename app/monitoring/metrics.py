"""Prometheus metrics for monitoring."""

from prometheus_client import Counter, Histogram

# Conversation metrics
conversations_total = Counter(
    "conversations_total", "Total number of conversations created"
)
messages_total = Counter("messages_total", "Total number of messages processed")
message_errors_total = Counter(
    "message_errors_total", "Total number of message processing errors"
)

# Response generation metrics
response_latency_seconds = Histogram(
    "response_latency_seconds",
    "Response generation latency in seconds",
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
)
response_duration_seconds = Histogram(
    "response_duration_seconds",
    "Response processing duration",
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
)

# Token metrics
tokens_used_total = Counter("tokens_used_total", "Total tokens used")
context_tokens_total = Counter("context_tokens_total", "Total context tokens used")
response_tokens_total = Counter("response_tokens_total", "Total response tokens used")
compression_events_total = Counter(
    "compression_events_total", "Total number of context compression events"
)

# Memory metrics
memory_retrieval_duration_seconds = Histogram(
    "memory_retrieval_duration_seconds",
    "Memory retrieval duration",
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0],
)
semantic_search_duration_seconds = Histogram(
    "semantic_search_duration_seconds",
    "Semantic memory search duration",
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0],
)
summarization_duration_seconds = Histogram(
    "summarization_duration_seconds",
    "Conversation summarization duration",
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0],
)

# Summary metrics
summaries_created_total = Counter(
    "summaries_created_total", "Total number of summaries created"
)
summary_tokens_saved_total = Counter(
    "summary_tokens_saved_total", "Total tokens saved through summarization"
)

