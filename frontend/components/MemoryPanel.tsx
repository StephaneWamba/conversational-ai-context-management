'use client';

import { useState, useEffect } from 'react';
import { apiService, type MemoryResponse } from '@/lib/api';

interface MemoryPanelProps {
  conversationId: string;
  showSummariesOnly?: boolean;
  showMemoryOnly?: boolean;
}

export default function MemoryPanel({ 
  conversationId, 
  showSummariesOnly = false,
  showMemoryOnly = false 
}: MemoryPanelProps) {
  const [memory, setMemory] = useState<MemoryResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchMemory = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const data = await apiService.getMemory(conversationId);
        setMemory(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch memory');
      } finally {
        setIsLoading(false);
      }
    };

    if (conversationId) {
      fetchMemory();
      const interval = setInterval(fetchMemory, 5000); // Refresh every 5 seconds
      return () => clearInterval(interval);
    }
  }, [conversationId]);

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border p-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          {showSummariesOnly ? 'Summaries' : 'Memory State'}
        </h3>
        <div className="text-sm text-gray-500">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-sm border p-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          {showSummariesOnly ? 'Summaries' : 'Memory State'}
        </h3>
        <div className="text-sm text-red-500">Error: {error}</div>
      </div>
    );
  }

  if (!memory) {
    return null;
  }

  // Show only summaries
  if (showSummariesOnly) {
    return (
      <div className="space-y-2 max-h-96 overflow-y-auto">
        {memory.summaries && memory.summaries.length > 0 ? (
          memory.summaries.map((summary, index) => (
            <div key={index} className="bg-green-50 rounded p-3 border border-green-200">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-semibold text-green-700">
                  Turns {summary.turn_range[0]}-{summary.turn_range[1]}
                </span>
              </div>
              <p className="text-xs text-gray-700 mt-1 line-clamp-4">
                {summary.summary}
              </p>
            </div>
          ))
        ) : (
          <div className="text-sm text-gray-500 text-center py-4">
            No summaries yet. Summaries are created every 5 turns.
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border p-4">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Memory State</h3>

      <div className="space-y-4">
        {/* Total Turns */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">Total Turns</span>
          </div>
          <div className="bg-indigo-50 rounded p-3">
            <p className="text-2xl font-bold text-indigo-600">{memory.total_turns}</p>
            <p className="text-xs text-gray-600 mt-1">Total conversation turns</p>
          </div>
        </div>

        {/* Short-term Memory */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">Short-term Memory</span>
            <span className="text-sm text-gray-500">(Redis)</span>
          </div>
          <div className="bg-blue-50 rounded p-3">
            <p className="text-2xl font-bold text-blue-600">{memory.short_term_turns}</p>
            <p className="text-xs text-gray-600 mt-1">Recent turns stored</p>
          </div>
        </div>

        {/* Long-term Memory */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">Long-term Memory</span>
            <span className="text-sm text-gray-500">(PostgreSQL)</span>
          </div>
          <div className="bg-green-50 rounded p-3">
            <p className="text-2xl font-bold text-green-600">{memory.long_term_summaries}</p>
            <p className="text-xs text-gray-600 mt-1">Summaries created</p>
          </div>
        </div>

        {/* Semantic Memory */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">Semantic Memory</span>
            <span className="text-sm text-gray-500">(Qdrant)</span>
          </div>
          <div className="bg-purple-50 rounded p-3">
            <p className="text-2xl font-bold text-purple-600">{memory.semantic_results}</p>
            <p className="text-xs text-gray-600 mt-1">Relevant past conversations</p>
          </div>
        </div>

        {/* Token Usage */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">Context Tokens</span>
          </div>
          <div className="bg-gray-50 rounded p-3">
            <p className="text-2xl font-bold text-gray-700">{memory.total_context_tokens}</p>
            <p className="text-xs text-gray-600 mt-1">Total tokens in context</p>
          </div>
        </div>

      </div>
    </div>
  );
}

