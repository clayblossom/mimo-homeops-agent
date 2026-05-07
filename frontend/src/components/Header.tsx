import { useEffect, useState } from 'react';
import { api, HealthResponse } from '../api';

export function Header() {
  const [health, setHealth] = useState<HealthResponse | null>(null);

  useEffect(() => {
    api.health().then(setHealth).catch(() => {});
  }, []);

  return (
    <header className="bg-xiaomi-darker border-b border-gray-700/50">
      <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-xiaomi-orange rounded-xl flex items-center justify-center text-xl font-bold">
            M
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">MiMo HomeOps Agent Pro</h1>
            <p className="text-xs text-gray-400">AI Smart Home Command Center</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          {health && (
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
              <span className="text-xs text-gray-400">
                v{health.version} • {health.device_count} devices • {Math.floor(health.uptime_seconds / 60)}m uptime
              </span>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
