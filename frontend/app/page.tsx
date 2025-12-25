'use client';

import { useState, useEffect } from 'react';
import ChatInterface from '@/components/ChatInterface';
import MemoryPanel from '@/components/MemoryPanel';
import MetricsPanel from '@/components/MetricsPanel';
import { apiService, type HealthStatus } from '@/lib/api';

export default function Home() {
  const [healthStatus, setHealthStatus] = useState<HealthStatus | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const status = await apiService.getHealth();
        setHealthStatus(status);
      } catch (error) {
        console.error('Failed to fetch health:', error);
        setHealthStatus({
          status: 'unhealthy',
          services: {},
        });
      }
    };

    fetchHealth();
    const interval = setInterval(fetchHealth, 10000); // Check every 10 seconds
    return () => clearInterval(interval);
  }, []);

  const isHealthy = healthStatus?.status === 'healthy';

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                Conversational AI Context Management
              </h1>
              <p className="text-sm text-gray-600 mt-1">
                Test long conversations with hierarchical memory, context compression, and token budgeting
              </p>
            </div>
            <div className="flex items-center gap-2">
              <div
                className={`w-3 h-3 rounded-full ${
                  isHealthy ? 'bg-green-500' : 'bg-red-500'
                }`}
              />
              <span className="text-sm text-gray-600">
                {isHealthy ? 'System Healthy' : 'System Degraded'}
              </span>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-[1920px] mx-auto px-4 py-6 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Sidebar - Summaries and System Health */}
          <div className="lg:col-span-3 space-y-6">
            {conversationId && (
              <div className="bg-white rounded-lg shadow-sm border p-4">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Summaries</h3>
                <MemoryPanel conversationId={conversationId} showSummariesOnly={true} />
              </div>
            )}
            <MetricsPanel healthStatus={healthStatus} />
          </div>

          {/* Center - Chat Interface */}
          <div className="lg:col-span-6">
            <ChatInterface
              conversationId={conversationId}
              onConversationCreated={setConversationId}
            />
          </div>

          {/* Right Sidebar - Memory State */}
          <div className="lg:col-span-3">
            {conversationId && (
              <MemoryPanel conversationId={conversationId} showMemoryOnly={true} />
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
