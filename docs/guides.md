# Setup, Deployment & Troubleshooting

Complete guide to setting up, deploying, and troubleshooting the Conversational AI Context Management system.

## Prerequisites

Before you begin, ensure you have:

- **Docker and Docker Compose**: For running all services
- **OpenAI API Key**: For embeddings, LLM generation, and summarization
- **4GB+ RAM**: Required for PostgreSQL, Redis, and Qdrant
- **Python 3.11+**: For running scripts (if needed)

## Quick Start

### 1. Clone and Setup

```bash
cd tutorials/conversational-ai-context-management

# Create .env file with your OpenAI API key
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### 2. Start Services

```bash
docker compose up -d
```

This starts all services:

- PostgreSQL (long-term memory storage)
- Redis (short-term memory cache)
- Qdrant (semantic memory vector database)
- Conversational AI Service (main API)
- Prometheus (monitoring)

Wait for all services to be healthy (check with `docker compose ps`).

### 3. Verify Services

Check that all services are running:

```bash
# Check service health
curl http://localhost:8006/health

# Check Qdrant
curl http://localhost:6339/collections

# Check Redis
docker compose exec redis redis-cli ping
```

### 4. Test the System

Start a conversation and test memory retention:

```bash
# Send a message
curl -X POST http://localhost:8006/api/conversations \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-1",
    "message": "My name is Alice and I like Python programming"
  }'

# Continue conversation (should remember name)
curl -X POST http://localhost:8006/api/conversations/{conversation_id}/messages \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What did I tell you about my name?"
  }'
```

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Key environment variables:

- **OPENAI_API_KEY** (required): Your OpenAI API key for embeddings, LLM, and summarization
- **POSTGRES_URL**: PostgreSQL connection string (default: `postgresql://postgres:postgres@postgres:5432/conversations`)
- **REDIS_URL**: Redis cache URL (default: `redis://redis:6379`)
- **QDRANT_URL**: Qdrant vector database URL (default: `http://qdrant:6333`)
- **LLM_MODEL**: OpenAI model for responses (default: `gpt-4o-mini`)
- **EMBEDDING_MODEL**: OpenAI model for embeddings (default: `text-embedding-3-small`)

All configuration options are documented in `app/core/config.py` with sensible defaults.

### Port Mappings

| Service                   | External Port | Internal Port | URL                           |
| ------------------------- | ------------- | ------------- | ----------------------------- |
| PostgreSQL                | 5440          | 5432          | `postgresql://localhost:5440` |
| Redis                     | 6385          | 6379          | `redis://localhost:6385`      |
| Qdrant                    | 6339          | 6333          | `http://localhost:6339`       |
| Conversational AI Service | 8006          | 8000          | `http://localhost:8006`       |

## API Endpoints

### Conversation API (`http://localhost:8006`)

- **`POST /api/conversations`**: Start a new conversation

  ```json
  {
    "user_id": "user-1",
    "message": "Hello, I need help with Python"
  }
  ```

- **`POST /api/conversations/{conversation_id}/messages`**: Send a message in an existing conversation

  ```json
  {
    "message": "Can you help me with async programming?"
  }
  ```

- **`GET /api/conversations/{conversation_id}`**: Get conversation details and memory state

- **`GET /api/conversations/{conversation_id}/memory`**: Get memory state (short-term, long-term, semantic)

- **`GET /health`**: Health check with dependency status

- **`GET /ready`**: Readiness probe (Kubernetes)

- **`GET /metrics`**: Prometheus metrics

## Development

### Running Services Locally

Services run in Docker containers with hot-reload enabled for development:

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f conversational-ai-service

# Restart a service
docker compose restart conversational-ai-service
```

### Running Scripts

```bash
# Test memory retention
docker compose exec conversational-ai-service python scripts/test_memory_retention.py

# Test API
docker compose exec conversational-ai-service python scripts/test_api.py
```

### Frontend UI

A Next.js frontend is included to demonstrate the system:

```bash
cd frontend
npm install
npm run dev
```

The frontend provides:

- **Chat Interface**: Interactive conversation UI
- **Memory Panel**: View short-term, long-term, and semantic memory
- **Summaries Panel**: View conversation summaries
- **Metrics Panel**: Monitor token usage and conversation stats

## Troubleshooting

### Qdrant Connection Errors

**Symptoms**: Semantic search failing, "connection refused" errors.

**Solutions**:

1. Verify Qdrant is running:

   ```bash
   docker compose ps qdrant
   ```

2. Check Qdrant logs:

   ```bash
   docker compose logs qdrant
   ```

3. Verify collection exists:

   ```bash
   curl http://localhost:6339/collections
   ```

4. Test connection:
   ```bash
   curl http://localhost:6339/health
   ```

### Qdrant Version Compatibility

**Symptoms**: `AttributeError: 'AsyncQdrantClient' object has no attribute 'search'`

**Problem**: Qdrant server 1.7.0 doesn't support the `query_points` API that newer client libraries expect.

**Solution**: The system uses REST API directly with httpx. If you see this error, ensure you're using the REST API implementation in `app/services/semantic_memory.py`.

### Redis Connection Errors

**Symptoms**: Short-term memory not working, "connection refused" errors.

**Solutions**:

1. Verify Redis is running:

   ```bash
   docker compose ps redis
   ```

2. Test connection:

   ```bash
   docker compose exec redis redis-cli ping
   ```

3. Check Redis logs:
   ```bash
   docker compose logs redis
   ```

### Semantic Search Returns 0 Results

**Symptoms**: Collection has points but search returns empty, even with low min_score.

**Solutions**:

1. Check filter format matches Qdrant REST API spec
2. Verify user_id filter syntax
3. Lower min_score to 0.5 for better recall (default is 0.7)
4. Check that summaries are being indexed:

   ```bash
   curl http://localhost:6333/collections/conversations/points/scroll
   ```

### Token Counting Issues

**Symptoms**: Estimated tokens don't match actual LLM usage, causing budget overruns.

**Solutions**:

- Ensure tiktoken is being used (not character count estimation)
- Verify model encoding matches your LLM model
- Check token budget calculations in `app/services/token_manager.py`

### Summarization Not Working

**Symptoms**: Summaries not being created every 10 turns.

**Solutions**:

1. Check if turn number is divisible by summary_interval (default: 10)
2. Verify PostgreSQL connection
3. Check service logs for summarization errors:

   ```bash
   docker compose logs conversational-ai-service | grep summary
   ```

4. Verify OpenAI API key is set correctly

### High Token Usage

**Symptoms**: Token costs higher than expected.

**Solutions**:

- Check compression threshold (default: 80% of budget)
- Verify compression is being triggered
- Review conversation length—compression benefits increase with longer conversations
- Check if semantic search is returning too many results (reduce limit)

### Memory Not Persisting

**Symptoms**: Conversation context lost between sessions.

**Solutions**:

1. Verify PostgreSQL is persisting data:

   ```bash
   docker compose exec postgres psql -U postgres -d conversations \
     -c "SELECT COUNT(*) FROM summaries;"
   ```

2. Check Redis TTL settings (default: 1 hour)
3. Verify Qdrant is persisting vectors
4. Check service logs for database errors

## Monitoring

### Prometheus

Access Prometheus at `http://localhost:9090` (if configured):

- Query metrics: `conversation_tokens_total`, `conversation_turns_total`, `memory_retrieval_duration_seconds`, etc.
- View conversation statistics
- Monitor token usage trends

### Key Metrics to Monitor

- **Token Usage**: Track tokens per conversation, compression effectiveness
- **Memory Retrieval Duration**: Should be <500ms for typical queries
- **Summary Creation Duration**: Should be <3 seconds
- **Semantic Search Results**: Number of relevant past conversations retrieved
- **Error Rate**: Should be <1% of total operations

## Limitations

- **Qdrant Version**: System tested with Qdrant 1.7.0 (uses REST API for compatibility)
- **Redis TTL**: Short-term memory expires after 1 hour (configurable)
- **Summary Interval**: Summaries created every 10 turns (configurable)
- **Compression Threshold**: Compression triggers at 80% of token budget (configurable)
- **Semantic Search**: Requires embeddings, adds latency (~200-500ms)

## Additional Resources

- **Architecture**: See [docs/architecture.md](architecture.md) for detailed system design
- **Frontend**: See `frontend/README.md` for frontend setup instructions
