# Conversational AI Context Management Frontend

Minimalist UI for demonstrating Conversational AI Context Management system capabilities.

## Features

- **Chat Interface**: Interactive conversation UI with message history
- **Memory Panel**: View short-term (Redis), long-term (PostgreSQL), and semantic (Qdrant) memory
- **Summaries Panel**: View conversation summaries created every 10 turns
- **Metrics Panel**: Monitor token usage, conversation stats, and memory retrieval performance

## Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:3000`.

## Environment Variables

Create a `.env.local` file in the `frontend` directory:

```
NEXT_PUBLIC_API_URL=http://localhost:8006
```

**Note**: The API URL should match your backend service port (default: 8006 from docker-compose.yml).

## Tech Stack

- **Next.js 16**: React framework with App Router
- **React 19**: UI library
- **TypeScript**: Type safety
- **Tailwind CSS**: Styling
- **Custom Components**: ChatInterface, MemoryPanel, MetricsPanel, SummariesPanel

## Usage

1. **Start the backend services** (see main README.md):
   ```bash
   docker compose up -d
   ```

2. **Start the frontend**:
   ```bash
   cd frontend
   npm run dev
   ```

3. **Open the UI**: Navigate to `http://localhost:3000`

4. **Start a conversation**: Enter a message in the chat interface

5. **View memory**: Use the Memory Panel to see:
   - Short-term memory (last 10 turns from Redis)
   - Long-term memory (summaries from PostgreSQL)
   - Semantic memory (relevant past conversations from Qdrant)

6. **Monitor metrics**: Check the Metrics Panel for:
   - Token usage per conversation
   - Conversation turn count
   - Memory retrieval duration
   - Summary creation stats

## Components

### ChatInterface

Main conversation UI component that:
- Displays message history
- Handles user input
- Shows assistant responses
- Displays token usage per message

### MemoryPanel

Shows the three memory layers:
- **Short-Term**: Recent turns from Redis cache
- **Long-Term**: Summaries from PostgreSQL
- **Semantic**: Relevant past conversations from Qdrant

### SummariesPanel

Displays conversation summaries:
- Summary text
- Turn range (e.g., turns 1-10)
- Compressed token count
- Creation timestamp

### MetricsPanel

Monitors system performance:
- Total tokens used
- Conversation turn count
- Memory retrieval latency
- Summary creation frequency

## API Integration

The frontend communicates with the backend API at `NEXT_PUBLIC_API_URL`:

- **`POST /api/conversations`**: Start new conversation
- **`POST /api/conversations/{id}/messages`**: Send message
- **`GET /api/conversations/{id}`**: Get conversation details
- **`GET /api/conversations/{id}/memory`**: Get memory state

See `lib/api.ts` for API client implementation.

## Development

### Running in Development Mode

```bash
npm run dev
```

### Building for Production

```bash
npm run build
npm start
```

### Linting

```bash
npm run lint
```

## Troubleshooting

### API Connection Errors

**Symptoms**: Frontend can't connect to backend API.

**Solutions**:

1. Verify backend is running:
   ```bash
   curl http://localhost:8006/health
   ```

2. Check `NEXT_PUBLIC_API_URL` in `.env.local` matches backend port

3. Ensure CORS is configured in backend (if needed)

### Memory Panel Empty

**Symptoms**: Memory Panel shows no data.

**Solutions**:

1. Verify conversation has enough turns (summaries created every 10 turns)
2. Check backend logs for memory retrieval errors
3. Verify Redis, PostgreSQL, and Qdrant are running

### Metrics Not Updating

**Symptoms**: Metrics Panel shows stale data.

**Solutions**:

1. Refresh the page
2. Check backend metrics endpoint: `curl http://localhost:8006/metrics`
3. Verify Prometheus is running (if configured)

