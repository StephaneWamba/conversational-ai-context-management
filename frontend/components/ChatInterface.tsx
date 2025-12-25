'use client';

import { useState, useRef, useEffect } from 'react';
import { apiService, type MessageResponse } from '@/lib/api';

interface ChatInterfaceProps {
  conversationId: string | null;
  onConversationCreated: (id: string) => void;
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
  turnNumber?: number;
  tokensUsed?: number;
  contextTokens?: number;
}

export default function ChatInterface({
  conversationId,
  onConversationCreated,
}: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [userId] = useState(() => `user_${Date.now()}`);
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(
    conversationId
  );
  const [cumulativeTokens, setCumulativeTokens] = useState(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setCurrentConversationId(conversationId);
  }, [conversationId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput('');
    setIsLoading(true);

    // Add user message to UI
    const newUserMessage: Message = {
      role: 'user',
      content: userMessage,
    };
    setMessages((prev) => [...prev, newUserMessage]);

    try {
      let response: MessageResponse;

      if (!currentConversationId) {
        // Create new conversation
        const result = await apiService.createConversation({
          user_id: userId,
          content: userMessage,
        });
        setCurrentConversationId(result.conversation.id);
        onConversationCreated(result.conversation.id);

        // Add assistant response from the backend
        const assistantMessage: Message = {
          role: 'assistant',
          content: result.message.response,
          turnNumber: result.message.turn_number,
          tokensUsed: result.message.tokens_used,
          contextTokens: result.message.context_tokens,
        };
        setMessages((prev) => [...prev, assistantMessage]);
        setCumulativeTokens((prev) => prev + (result.message.tokens_used || 0));
        setIsLoading(false);
        return;
      } else {
        // Send message to existing conversation
        response = await apiService.sendMessage(currentConversationId, {
          user_id: userId,
          content: userMessage,
        });
      }

      // Add assistant response to UI
      const assistantMessage: Message = {
        role: 'assistant',
        content: response.response,
        turnNumber: response.turn_number,
        tokensUsed: response.tokens_used,
        contextTokens: response.context_tokens,
      };
      setMessages((prev) => [...prev, assistantMessage]);
      setCumulativeTokens((prev) => prev + (response.tokens_used || 0));
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: Message = {
        role: 'assistant',
        content: `Error: ${error instanceof Error ? error.message : 'Failed to send message'}`,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border h-[600px] flex flex-col">
      <div className="p-4 border-b">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Chat</h2>
            {currentConversationId && (
              <p className="text-xs text-gray-500 mt-1">
                Conversation ID: {currentConversationId.slice(0, 8)}...
              </p>
            )}
          </div>
          {cumulativeTokens > 0 && (
            <div className="text-right">
              <p className="text-sm font-medium text-gray-700">Cumulative Tokens</p>
              <p className="text-lg font-bold text-blue-600">{cumulativeTokens.toLocaleString()}</p>
            </div>
          )}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-8">
            <p>Start a conversation by typing a message below.</p>
            <p className="text-sm mt-2">
              The system will maintain context across multiple turns using hierarchical memory.
            </p>
          </div>
        )}

        {messages.map((message, index) => (
          <div
            key={index}
            className={`flex ${
              message.role === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            <div
              className={`max-w-[80%] rounded-lg px-4 py-2 ${
                message.role === 'user'
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-100 text-gray-900'
              }`}
            >
              <p className="whitespace-pre-wrap">{message.content}</p>
              {message.tokensUsed && (
                <p className="text-xs mt-1 opacity-70">
                  Turn {message.turnNumber} • {message.tokensUsed} tokens
                  {message.contextTokens && ` (context: ${message.contextTokens})`}
                </p>
              )}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg px-4 py-2">
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="p-4 border-t">
        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message... (Press Enter to send)"
            className="flex-1 resize-none border rounded-lg px-3 py-2 text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
            rows={2}
            disabled={isLoading}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}

