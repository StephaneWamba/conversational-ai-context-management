'use client';

import { type HealthStatus } from '@/lib/api';

interface MetricsPanelProps {
  healthStatus: HealthStatus | null;
}

export default function MetricsPanel({ healthStatus }: MetricsPanelProps) {
  if (!healthStatus) {
    return (
      <div className="bg-white rounded-lg shadow-sm border p-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">System Health</h3>
        <div className="text-sm text-gray-500">Loading...</div>
      </div>
    );
  }

  const services = healthStatus.services || {};

  const getStatusColor = (status?: string) => {
    if (status === 'healthy') return 'text-green-600 bg-green-50';
    if (status === 'unhealthy') return 'text-red-600 bg-red-50';
    return 'text-yellow-600 bg-yellow-50';
  };

  const getStatusIcon = (status?: string) => {
    if (status === 'healthy') return '✓';
    if (status === 'unhealthy') return '✗';
    return '?';
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border p-4">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">System Health</h3>

      <div className="space-y-3">
        {/* PostgreSQL */}
        <div className="flex items-center justify-between p-2 rounded">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-gray-700">PostgreSQL</span>
          </div>
          <div
            className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(
              services.postgres?.status
            )}`}
          >
            {getStatusIcon(services.postgres?.status)} {services.postgres?.status || 'unknown'}
          </div>
        </div>

        {/* Qdrant */}
        <div className="flex items-center justify-between p-2 rounded">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-gray-700">Qdrant</span>
          </div>
          <div
            className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(
              services.qdrant?.status
            )}`}
          >
            {getStatusIcon(services.qdrant?.status)} {services.qdrant?.status || 'unknown'}
          </div>
        </div>

        {/* Redis */}
        <div className="flex items-center justify-between p-2 rounded">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-gray-700">Redis</span>
          </div>
          <div
            className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(
              services.redis?.status
            )}`}
          >
            {getStatusIcon(services.redis?.status)} {services.redis?.status || 'unknown'}
          </div>
        </div>

        {/* OpenAI */}
        <div className="flex items-center justify-between p-2 rounded">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-gray-700">OpenAI</span>
          </div>
          <div
            className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(
              services.openai?.status
            )}`}
          >
            {getStatusIcon(services.openai?.status)} {services.openai?.status || 'unknown'}
          </div>
        </div>

        {/* Latency Info */}
        {(services.postgres?.latency_ms ||
          services.qdrant?.latency_ms ||
          services.redis?.latency_ms ||
          services.openai?.latency_ms) && (
          <div className="mt-4 pt-4 border-t">
            <p className="text-xs text-gray-500 mb-2">Latency (ms):</p>
            <div className="space-y-1 text-xs text-gray-600">
              {services.postgres?.latency_ms && (
                <div>PostgreSQL: {services.postgres.latency_ms.toFixed(2)}ms</div>
              )}
              {services.qdrant?.latency_ms && (
                <div>Qdrant: {services.qdrant.latency_ms.toFixed(2)}ms</div>
              )}
              {services.redis?.latency_ms && (
                <div>Redis: {services.redis.latency_ms.toFixed(2)}ms</div>
              )}
              {services.openai?.latency_ms && (
                <div>OpenAI: {services.openai.latency_ms.toFixed(2)}ms</div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

