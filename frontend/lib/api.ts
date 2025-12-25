/**
 * API service for communicating with the conversation service backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8006';

export interface MessageRequest {
  user_id: string;
  session_id?: string;
  content: string;
}

export interface MessageResponse {
  conversation_id: string;
  message_id: string;
  response: string;
  turn_number: number;
  tokens_used: number;
  context_tokens: number;
  response_tokens: number;
}

export interface ConversationResponse {
  id: string;
  user_id: string;
  session_id: string;
  total_turns: number;
  total_tokens_used: number;
  created_at: string;
  updated_at: string;
}

export interface CreateConversationResponse {
  conversation: ConversationResponse;
  message: MessageResponse;
}

export interface MemoryResponse {
  conversation_id: string;
  short_term_turns: number;
  long_term_summaries: number;
  semantic_results: number;
  total_context_tokens: number;
  total_turns: number;
  summaries: Array<{
    turn_range: [number, number];
    summary: string;
    key_facts?: Record<string, unknown>;
  }>;
}

export interface HealthStatus {
  status: string;
  services: {
    postgres?: { status: string; latency_ms?: number; error?: string };
    qdrant?: { status: string; latency_ms?: number; error?: string };
    redis?: { status: string; latency_ms?: number; error?: string };
    openai?: { status: string; latency_ms?: number; error?: string };
  };
}

class ApiService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = API_BASE_URL;
  }

  async createConversation(request: MessageRequest): Promise<CreateConversationResponse> {
    const response = await fetch(`${this.baseUrl}/api/conversations`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create conversation');
    }

    return response.json();
  }

  async sendMessage(
    conversationId: string,
    request: MessageRequest
  ): Promise<MessageResponse> {
    const response = await fetch(
      `${this.baseUrl}/api/conversations/${conversationId}/messages`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to send message');
    }

    return response.json();
  }

  async getConversation(conversationId: string): Promise<ConversationResponse> {
    const response = await fetch(
      `${this.baseUrl}/api/conversations/${conversationId}`
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get conversation');
    }

    return response.json();
  }

  async getMemory(conversationId: string): Promise<MemoryResponse> {
    const response = await fetch(
      `${this.baseUrl}/api/conversations/${conversationId}/memory`
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get memory');
    }

    return response.json();
  }

  async getHealth(): Promise<HealthStatus> {
    const response = await fetch(`${this.baseUrl}/health`);

    if (!response.ok) {
      return {
        status: 'unhealthy',
        services: {},
      };
    }

    const data = await response.json();
    return typeof data === 'string' ? JSON.parse(data) : data;
  }
}

export const apiService = new ApiService();

