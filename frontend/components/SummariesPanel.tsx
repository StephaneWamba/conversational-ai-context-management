'use client';

import { useState, useEffect } from 'react';
import { apiService, type MemoryResponse } from '@/lib/api';

interface SummariesPanelProps {
  conversationId: string;
}

export default function SummariesPanel({ conversationId }: SummariesPanelProps) {
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
        setError(err instanceof Error ? err.message : 'Failed to fetch summaries');
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
    return <div className="text-sm text-gray-500">Loading summaries...</div>;
  }

  if (error) {
    return <div className="text-sm text-red-500">Error: {error}</div>;
  }

  if (!memory || !memory.summaries || memory.summaries.length === 0) {
    return (
      <div className="text-sm text-gray-500">
        No summaries yet. Summaries are created every 10 turns.
      </div>
    );
  }

  return (
    <div className="space-y-3 max-h-[600px] overflow-y-auto">
      {memory.summaries.map((summary, index) => (
        <div key={index} className="bg-green-50 rounded-lg p-3 border border-green-200">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-green-700">
              Turns {summary.turn_range[0]}-{summary.turn_range[1]}
            </span>
          </div>
          <p className="text-xs text-gray-700 mt-1 line-clamp-4">
            {summary.summary}
          </p>
        </div>
      ))}
    </div>
  );
}

